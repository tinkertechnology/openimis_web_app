import django
import uuid 
import graphene
from datetime import timedelta, date
from insuree import models as insuree_models
from claim import models as claim_models
from graphene_django import DjangoObjectType
from .models import InsureeAuth, Notice, HealthFacilityCoordinate
# We do need all queries and mutations in the namespace here.
# from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutations import *  # lgtm [py/polluting-import]


class InsureeHolderGQLType(DjangoObjectType):
    class Meta:
        model = insuree_models.Insuree
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
    class Meta:
        model = InsureeAuth
        fields = ['id', 'token', 'insuree']

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
        fields = ['id','chf_id', 'other_names', 'last_name', 'insuree_policies', 'insuree_claim', 'recent_policy', 'remaining_days']


    insuree_claim = graphene.List(InsureeClaimGQLType)
    insuree_policies = graphene.List(InsureePolicyType)
    recent_policy = graphene.Field(InsureePolicyType)
    remaining_days = graphene.String()
    def resolve_photos(value_obj,info):
        return value_obj.photos.all
    
    def resolve_insuree_policies(value_obj, info):
        return value_obj.insuree_policies.all()
    def resolve_insuree_claim(value_obj, info):
        # return value_obj.insuree.all()
        return claim_models.Claim.objects.filter(insuree=value_obj)
    
    def resolve_recent_policy(value_obj, info):
        latest_policy = insuree_models.InsureePolicy.objects.filter(insuree=value_obj).order_by('-expiry_date').first()
        return latest_policy
    
    def resolve_remaining_days(value_obj, info):
        latest_policy = insuree_models.InsureePolicy.objects.filter(insuree=value_obj).order_by('-expiry_date').first()
        remaining_days = (latest_policy.expiry_date-date.today()).days
        return remaining_days


class NoticeGQLType(DjangoObjectType):
    class Meta:
        model = Notice
        interfaces = (graphene.relay.Node,)
        fields= ['id', 'title', 'description', 'created_at']

class HealthFacilityCoordinateGQLType(DjangoObjectType):
    class Meta:
        model = HealthFacilityCoordinate
        interfaces = (graphene.relay.Node,)
        fields= '__all__'

from django.core.exceptions import PermissionDenied

class Query(graphene.ObjectType):
    password = graphene.String()
    insuree_auth = graphene.Field(InsureeAuthGQLType, insureeCHFID=graphene.String(), familyHeadCHFID=graphene.String(), dob=graphene.Date())
    insuree_auth_otp = graphene.Field(InsureeAuthGQLType, chfid=graphene.String(), otp=graphene.String())
    insuree_profile = graphene.Field(InsureeProfileGQLType, insureeCHFID=graphene.Int())
    insuree_claim = graphene.List(InsureeClaimGQLType, claimId=graphene.Int())
    notices = graphene.List(NoticeGQLType)
    health_facility_coordinate=graphene.List(HealthFacilityCoordinateGQLType, inputLatitude=graphene.Decimal(), inputLongitude=graphene.Decimal() )


    def resolve_insuree_auth(self, info, insureeCHFID, familyHeadCHFID, dob,  **kwargs):
        auth=False
        insuree_auth_obj=None
        insuree_obj = insuree_models.Insuree.objects.filter(chf_id=insureeCHFID).filter(dob=dob).first()        
        if insuree_obj:
            familty_insuree_obj = insuree_models.Insuree.objects.filter(chf_id=familyHeadCHFID).filter(head=True).first()
            if familty_insuree_obj:
                if insuree_obj.family==familty_insuree_obj.family:
                    auth=True
        if auth==True:
            insuree_auth_obj = InsureeAuth.objects.filter(insuree=insuree_obj).first()
            if not insuree_auth_obj:
                insuree_auth_obj = InsureeAuth()
                insuree_auth_obj.insuree = insuree_obj
                insuree_auth_obj.save()
                insuree_auth_obj.token = uuid.uuid4().hex[:6].upper() + str(insuree_auth_obj.id) #todo yeslai lamo banaune
            insuree_auth_obj.otp = uuid.uuid4().hex[:4]
            insuree_auth_obj.save()
        if insuree_auth_obj:
            insuree_auth_obj.token = '' #user lai login garda otp verify agadi token nadine
        return insuree_auth_obj

    def resolve_insuree_claim(self, info, claimId):
        return claim_models.Claim.objects.filter(id=claimId)




    def resolve_insuree_auth_otp(self, info, chfid, otp):
        checkotp = InsureeAuth.objects.filter(otp=otp).filter(insuree__chf_id=chfid).first()
        if checkotp:
            return checkotp
        return None

    def resolve_insuree_profile(self, info, insureeCHFID,**kwargs):
        return insuree_models.Insuree.objects.get(id=insureeCHFID)

        # if insuree_obj:
        #     return InsureeVerifyGQLType(insuree_obj)
        # return ''
    def resolve_notices(self, info):
        return Notice.objects.filter(active=True)

    def generate_token(self):
        token = uuid.uuid4().hex[:6].upper()
        return token
    
    def resolve_health_facility_coordinate(self, info, inputLatitude, inputLongitude):
        return HealthFacilityCoordinate.objects.all()
        pass


class Mutation(graphene.ObjectType):
    create_notice = CreateNoticeMutation.Field()
    update_notice = UpdateNoticeMutation.Field()
    delete_notice = DeleteNoticeMutation.Field()
    create_voucher_payment = CreateVoucherPaymentMutation.Field()

    




