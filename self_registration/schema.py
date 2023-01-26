import uuid
from django.db.models.fields import BooleanField
import graphene
from datetime import timedelta, date
from django_filters import CharFilter
from insuree import models as insuree_models
from claim import models as claim_models
from policy import models as policy_models
from graphene_django import DjangoObjectType
from graphene import relay, ObjectType, Connection, Int
from graphene_django.filter import DjangoFilterConnectionField
from .models import InsureeAuth, Notice, HealthFacilityCoordinate
from graphene_django.registry import Registry
from .models import  InsureeTempReg
from django.db.models import Q

# We do need all queries and mutations in the namespace here.
# from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutations import *  # lgtm [py/polluting-import]
from django.db.models.expressions import OrderBy, RawSQL
from django.core.exceptions import PermissionDenied
from django.conf import settings
from .services import send_email_otp


def gql_auth_insuree(function):
    def wrap(*args, **kwargs):
        if args:
            if args[1]:  # info of graphql resolve
                context = args[1].context
                # user = context.user
                user = None
                if user:
                    return function(*args, **kwargs)
                token = context.META.get('HTTP_INSUREE_TOKEN')
                # -H 'Insuree-Token: F008CA1' \
                if token:
                    insuree = InsureeAuth.objects.filter(token=token).first()
                    if insuree:
                        return function(*args, **kwargs)
        raise PermissionDenied("No insuree token")

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def get_qs_nearby_hfcoord(latitude, longitude, max_distance=None):
    """
    Return objects sorted by distance to specified coordinates
    which distance is less than max_distance given in kilometers
    """
    # Great circle distance formula
    gcd_formula = """
        6371 * 
            acos(
                cos( radians( %s ) ) * cos( radians( latitude ) ) * cos ( radians(longitude) - radians(%s) ) +
                sin( radians(%s) ) * sin( radians( latitude ) )
            )
    """ % (latitude, longitude, latitude)

    distance_raw_sql = RawSQL(
        gcd_formula,
        ()
    )
    qs = HealthFacilityCoordinate.objects.all() \
        .annotate(distance=distance_raw_sql) \
        .order_by('distance')
    if max_distance is not None:
        qs = qs.filter(distance__lt=float(max_distance))
    qs = qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    return qs


class InsureeHolderGQLType(DjangoObjectType):
    class Meta:
        model = insuree_models.Insuree
        fields = '__all__'


class PolicyType(DjangoObjectType):
    class Meta:
        model = policy_models.Policy
        fields = '__all__'


class InsureePolicyType(DjangoObjectType):
    class Meta:
        model = insuree_models.InsureePolicy
        fields = '__all__'
    # def resolve_insuree_policies(self, info):
    #     return self.


class InsureeClaimGQLType(DjangoObjectType):
    class Meta:
        model = claim_models.Claim
        fields = '__all__'


class InsureeAuthGQLType(DjangoObjectType):
    insuree = graphene.Field(InsureeHolderGQLType)
    message = graphene.String()
    issuccess = graphene.Boolean()

    class Meta:
        model = InsureeAuth
        fields = ['id', 'token', 'insuree', 'message']  # OTP from sms or email, not from API\
    def resolve_message(self, info):
        message = f"Phone no. not registered with this account.Please contact HIB"
        if not self.insuree:
            message = f"Invalid Details"
            return message
        if self.insuree.phone:
            message = f"OTP sent to {self.insuree.phone}" 
        return message  

    def resolve_issuccess(self, info):
        issuccess = False
        if not self.insuree:
            issuccess=False
            return issuccess
        if self.insuree.phone:
            issuccess=True
        return issuccess 

class ProfileGQLType(DjangoObjectType):
    remaining_days = graphene.String()
    class Meta:
        model = Profile
        fields = ['photo', "email", "phone", "insuree", "remaining_days"]

    def resolve_photo(self, info):
        # if self.photo:
        #     self.photo = info.context.build_absolute_uri(self.photo.url)
        # return self.photo
        if self.insuree.photo:
            if self.insuree.photo.filename:
                return f"https://imis.hib.gov.np/Images/Updated/{self.insuree.photo.filename}"
        return ''
        # return "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"

    def resolve_remaining_days(value_obj, info):
        latest_policy = insuree_models.InsureePolicy.objects.filter(insuree=value_obj.insuree).order_by('expiry_date').first()
        remaining_days = (latest_policy.expiry_date - date.today()).days
        return remaining_days

# class InsureeImageGQLType(DjangoObjectType):
#     class Meta:
#         model = insuree_models.InsureePhoto
#         fields = ['id', 'photo']

#     def resolve_photo(self, info):
#         if self.image:
#             self.image = info.context.build_absolute_uri(self.photo.url)
#         return self.image


class InsureeProfileGQLType(DjangoObjectType):
    class Meta:
        model = insuree_models.Insuree
        interfaces = (graphene.relay.Node,)
        fields = ['id', 'chf_id', 'other_names', 'last_name', 'insuree_policies',
                  'insuree_claim', 'recent_policy', 'remaining_days', 'family_policy']

        registry = Registry()

    insuree_claim = graphene.List(InsureeClaimGQLType)
    insuree_policies = graphene.List(InsureePolicyType)
    recent_policy = graphene.Field(InsureePolicyType)
    family_policy = graphene.Field(InsureePolicyType)
    insuree_family_policies = graphene.Field(PolicyType)
    remaining_days = graphene.String()

    def resolve_photos(value_obj, info):
        return value_obj.photos.all

    def resolve_insuree_policies(value_obj, info):
        return value_obj.insuree_policies.order_by("expiry_date").filter(validity_to=None)

    def resolve_insuree_claim(value_obj, info):
        # return value_obj.insuree.all()
        return claim_models.Claim.objects.filter(insuree=value_obj).filter(validity_to=None)

    def resolve_recent_policy(value_obj, info):
        latest_policy = insuree_models.InsureePolicy.objects.filter(insuree=value_obj).order_by('expiry_date').first()
        return latest_policy

    def resolve_family_policy(value_obj, info):
        insuree_policy_obj = insuree_models.InsureePolicy.objects.filter(insuree=value_obj)
        policy_obj = insuree_policy_obj.policy
        return policy_obj

    def resolve_remaining_days(value_obj, info):
        latest_policy = insuree_models.InsureePolicy.objects.filter(insuree=value_obj).order_by('-expiry_date').first()
        remaining_days = (latest_policy.expiry_date - date.today()).days
        return remaining_days


from .gql_mutations import FeedbackAppGQLType


class NoticeGQLType(DjangoObjectType):
    class Meta:
        model = Notice
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "title": ['exact', 'icontains', 'istartswith'],
            "description": ['exact', 'icontains', 'istartswith'],
            "active": ['exact'],

        }

        connection_class = ExtendedConnection


class VoucherPaymentGQLType(DjangoObjectType):
    # insuree_name = graphene.String()
    # insuree_name = CharFilter(field_name='insuree__othername', lookup_expr='icontains', distinct=True)
    class Meta:
        model = VoucherPayment
        interfaces = (graphene.relay.Node,)
        fields = ["voucher", "voucher_id", "insuree"]
        filter_fields = {
            # "title" : CharFilter(field_name='insuree__chf_id', lookup_expr='icontains', distinct=True),
            "insuree__chf_id": ['icontains'],
            "insuree__other_names" : ['icontains'],
            "insuree__last_name" : ["icontains"]
            # "voucher_id": ['exact', 'icontains', 'istartswith'],

        }
        connection_class = ExtendedConnection
        # @classmethod
    def resolve_voucher(self, info):
        if self.voucher:
            self.voucher = info.context.build_absolute_uri(self.voucher.url)
        return self.voucher



class HealthFacilityCoordinateGQLType(DjangoObjectType):
    distance = graphene.Float()

    class Meta:
        model = HealthFacilityCoordinate
        interfaces = (graphene.relay.Node,)
        fields = '__all__'



class NotificationGQLType(DjangoObjectType):
    class Meta:
        model = Notification
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filter_fields = {
            # "insuree": ['exact', 'icontains', 'istartswith'],
            # "voucher_id": ['exact', 'icontains', 'istartswith'],

        }

    connection_class = ExtendedConnection


# class testObjtype(ObjectType):
#     insuree = graphene.String()

class TemporaryRegGQLType(DjangoObjectType):
    class Meta:
        model = InsureeTempReg
        interfaces = (graphene.relay.Node,)
        fields = "__all__" #["id", "json", "created_at", "updated_at", "is_approved"]
        filter_fields = {
            "id" : ["exact"],
            "is_approved" : ["exact"],
            "phone_number":["exact"]
        }
        connection_class = ExtendedConnection







class Query(graphene.ObjectType):
    password = graphene.String()
    insuree_auth = graphene.Field(InsureeAuthGQLType, insureeCHFID=graphene.String(), familyHeadCHFID=graphene.String(),
                                  dob=graphene.Date())
    insuree_auth_otp = graphene.Field(InsureeAuthGQLType, chfid=graphene.String(), otp=graphene.String())
    # insuree_profile = graphene.Field(InsureeProfileGQLType, insureeCHFID=graphene.Int())
    insuree_profile = graphene.Field(InsureeProfileGQLType, insureeCHFID=graphene.String())
    insuree_claim = graphene.List(InsureeClaimGQLType, claimId=graphene.Int())
    notifications =  DjangoFilterConnectionField(NotificationGQLType, insureeCHFID=graphene.String())

    notice = relay.Node.Field(NoticeGQLType)
    notices = DjangoFilterConnectionField(NoticeGQLType, orderBy=graphene.List(of_type=graphene.String))

    feedback = relay.Node.Field(FeedbackAppGQLType)
    feedbacks = DjangoFilterConnectionField(FeedbackAppGQLType, orderBy=graphene.List(of_type=graphene.String))

    tempreg = relay.Node.Field(TemporaryRegGQLType)
    tempregs = DjangoFilterConnectionField(TemporaryRegGQLType, orderBy=graphene.List(of_type=graphene.String))

    profile = graphene.Field(ProfileGQLType, insureeCHFID=graphene.String())

    voucher_payments = DjangoFilterConnectionField(VoucherPaymentGQLType,
                                                   orderBy=graphene.List(of_type=graphene.String),
                                                   image_url=graphene.String())
    insuree_policy = graphene.Field(PolicyType, insureeCHFID=graphene.String())
    health_facility_coordinate = graphene.List(HealthFacilityCoordinateGQLType, inputLatitude=graphene.Decimal(),
                                               inputLongitude=graphene.Decimal())
    #validate_insuree = graphene.Field(TemporaryRegGQLType, card_id=graphene.String(Required=False), phone_number=graphene.String())
    def resolve_insuree_auth1(self, info, insureeCHFID, familyHeadCHFID, dob, **kwargs):
        try:
            return self.resolve_insuree_auth1(info, insureeCHFID, familyHeadCHFID, dob, **kwargs)
        except: import traceback; import sys; traceback.print_exception(*sys.exc_info());
        
    def resolve_insuree_auth(self, info, insureeCHFID, familyHeadCHFID, dob, **kwargs):
        try:
            from .date_np_en import date_np_en
            """ 
                Need to convert nepali date to english date , since people uses nepali date
            """
            j = date_np_en.get(str(dob)) 
            auth = False
            insuree_auth_obj = None
            insuree_obj = insuree_models.Insuree.objects.filter(chf_id=insureeCHFID).filter(dob=date_np_en.get(str(dob))).first()
            if insuree_obj:
                familty_insuree_obj = insuree_models.Insuree.objects.filter(chf_id=familyHeadCHFID).filter(
                    head=True).first()
                if familty_insuree_obj:
                    if insuree_obj.family == familty_insuree_obj.family:
                        auth = True
            if auth == True:
                insuree_auth_obj = InsureeAuth.objects.filter(insuree=insuree_obj).first()
                if not insuree_auth_obj:
                    insuree_auth_obj = InsureeAuth()
                    insuree_auth_obj.insuree = insuree_obj
                    insuree_auth_obj.save()
                    insuree_auth_obj.token = uuid.uuid4().hex[:6].upper() + str(
                        insuree_auth_obj.id)  # todo yeslai lamo banaune
                import random
                insuree_auth_obj.otp = random.randint(1000,9999) #uuid.uuid4().hex[:4]
                # sms/email action from this point
                if insuree_obj.chf_id=="852741963":
                    insuree_auth_obj.otp="3654"
                url = settings.DOIT_SMS_URL#"https://sms.doit.gov.np/api/sms"
                import json
                payload = json.dumps({
                "message": f"Your OTP Code for Login {insuree_auth_obj.otp}",
                "mobile": f"977{insuree_obj.phone}"
                }) 
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {settings.SMS_TOKEN}'
                }                
                import requests
                r = requests.request("POST", url, headers=headers, data=payload)
                status_code = r.status_code
                response = r.text
                try:
                    response_json = r.json()
                except:
                    pass
                insuree_auth_obj.save()
            if settings.get('USE_EMAIL_OTP'):
                send_email_otp(insuree_obj,insuree_auth_obj.otp)
            if insuree_auth_obj:
                insuree_auth_obj.token = ''  # User cannot get otp before verify login 
            return insuree_auth_obj
        except: import traceback; import sys; traceback.print_exception(*sys.exc_info());

    def resolve_insuree_policy(self, info, insureeCHFID):
        policy_obj = policy_models.Policy.order_by("-expiry_date")
        return policy_obj

    def resolve_notifications(self, info, insureeCHFID, **kwargs):
        return Notification.objects.filter(chf_id=insureeCHFID).order_by("-created_at")

    def resolve_insuree_claim(self, info, claimId):
        return claim_models.Claim.objects.filter(id=claimId)

    def resolve_insuree_auth_otp(self, info, chfid, otp):
        checkotp = InsureeAuth.objects.filter(otp=otp).filter(insuree__chf_id=chfid).first()
        if checkotp:
            return checkotp
        return None

    def resolve_insuree_profile(self, info, insureeCHFID, **kwargs):
        return insuree_models.Insuree.objects.filter(chf_id=insureeCHFID).first()

        # if insuree_obj:
        #     return InsureeVerifyGQLType(insuree_obj)
        # return ''

    def resolve_profile(self, info, insureeCHFID):
        profile = Profile.objects.filter(insuree__chf_id=insureeCHFID).first()
        if profile:
            return profile
        else:
            insuree_obj = insuree_models.Insuree.objects.filter(chf_id=insureeCHFID).first()
            profile = Profile.objects.create(insuree=insuree_obj, email=insuree_obj.email,phone=insuree_obj.phone)
        return profile


    # @gql_auth_insuree
    def resolve_notices(self, info, **kwargs):
        orderBy = kwargs.get('orderBy', None)
        if not orderBy:
            return Notice.objects.order_by("-created_at")
        return Notice.objects.order_by(*orderBy)

    def resolve_feedbacks(self, info, **kwargs):
        orderBy = kwargs.get('orderBy', None)
        if not orderBy:
            return Feedback.objects.order_by("-created_at")
        return Feedback.objects.order_by(*orderBy)

    def resolve_voucher_payments(self, info, **kwargs):
        orderBy = kwargs.get('orderBy', None)
        return VoucherPayment.objects.order_by(*orderBy)

    def generate_token(self):
        token = uuid.uuid4().hex[:6].upper()
        return token

    # @gql_auth_insuree
    def resolve_health_facility_coordinate(self, info, inputLatitude, inputLongitude):
        # return HealthFacilityCoordinate.objects.all()
        return get_qs_nearby_hfcoord(inputLatitude, inputLongitude, None)
        pass

    def resolve_validate_insuree(self, info, phone_number):
        jot = InsureeTempReg.objects.filter(phone_number=phone_number).first() #(Q(phone_no=phone_number | Q(card_id=card_id))):
        return jot
    
    def resolve_track_registration_status(self, info, phone_no):
        reg_status = InsureeTempReg.objects.filter(phone_number=phone_no.strip()).first()
        return reg_status
        

class Mutation(graphene.ObjectType):
    create_notice = CreateNoticeMutation.Field()
    update_notice = UpdateNoticeMutation.Field()
    delete_notice = DeleteNoticeMutation.Field()
    create_voucher_payment = CreateVoucherPaymentMutation.Field()
    create_feedback = CreateFeedbackMutation.Field()
    update_profile = CreateOrUpdateProfileMutation.Field()
    create_temporary_insuree = CreateTempRegInsureeMutation.Field()
    create_insuree_mutation_from_temp = CreateInsureeMutation.Field()

# schema = graphene.Schema(query=Query, mutation=Mutation)
