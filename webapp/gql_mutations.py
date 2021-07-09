import base64
from django.core.files.base import ContentFile


import graphene
from core.schema import OpenIMISMutation
from graphql import GraphQLError


def dfprint(i):
    print(i)
    pass

# format base64 id string
def fbis64(inp):
    dfprint('fbis64')
    # NoticeGQLType:38
    # 
    bstr=base64.b64decode(inp)
    sstr=bstr.decode('utf-8')
    istrs=sstr.split(':')
    istr=istrs[1]
    dfprint([bstr, sstr, istr])
    return istr

# from graphene import relay, ObjectType

# from .apps import ClaimConfig
# from claim.validations import validate_claim, get_claim_category, validate_assign_prod_to_claimitems_and_services, \
#     process_dedrem, approved_amount
# from core import filter_validity, assert_string_length
# from core.schema import TinyInt, SmallInt, OpenIMISMutation
# from core.gql.gql_mutations import mutation_on_uuids_from_filter
# from django.conf import settings
# from django.contrib.auth.models import AnonymousUser
# from django.core.exceptions import ValidationError, PermissionDenied
# from django.utils.translation import gettext as _
# from graphene import InputObjectType
# from location.schema import UserDistrict

# from .gql_queries import ClaimGQLType
# from .models import Claim, Feedback, ClaimDetail, ClaimItem, ClaimService, ClaimAttachment, ClaimDedRem
# from product.models import ProductItemOrService

# logger = logging.getLogger(__name__)
from .models import Notice, VoucherPayment, Feedback
from graphene_django import DjangoObjectType
from graphene import Connection, Int
from insuree import models as insuree_models
import core


class ExtendedConnection(Connection):
    class Meta:
        abstract = True

    total_count = Int()
    edge_count = Int()

    def resolve_total_count(root, info, **kwargs):
        print(root.length)
        return root.length
    def resolve_edge_count(root, info, **kwargs):
        return len(root.edges)


class VoucherPaymentType(DjangoObjectType):
    class Meta:
        model = VoucherPayment
        fields = ['voucher']




from .models import Profile




class CreateOrUpdateProfileMutation(graphene.Mutation):
    # _mutation_module = "webapp"
    # _mutation_class = "CreateNoticeMutation"
    class Arguments(object):
        file = graphene.List(graphene.String)
        insureeCHFID = graphene.String() #basically chfid
        email = graphene.String()
        phone = graphene.String()
    ok = graphene.Boolean()
    # @classmethod
    def mutate (self, info, file, insureeCHFID, email, phone):
        files = info.context.FILES
        print(files)
        insuree_obj = insuree_models.Insuree.objects.filter(chf_id=insureeCHFID).first()
        print(insuree_obj.pk)
        instance = Profile.objects.filter(insuree_id=insuree_obj.pk).first()
        if not instance:
            print("1111")
            instance = Profile()
        instance.photo =  files.get('file')  if files.get('file') else instance.photo
        instance.email = email if email else instance.email
        instance.phone = phone if phone else instance.phone
        instance.save()
        return CreateOrUpdateProfileMutation(ok=True)






from .models import  Notification
class CreateVoucherPaymentMutation(graphene.Mutation):
    # _mutation_module = "webapp"
    # _mutation_class = "CreateNoticeMutation"
    class Arguments(object):
        file = graphene.List(graphene.String)
        insuree = graphene.String()
    ok = graphene.Boolean()
    # @classmethod
    def mutate (self, info, file, insuree):
        files = info.context.FILES
        # print(info.context)
        insuree_obj = insuree_models.Insuree.objects.filter(chf_id=insuree).first()
        VoucherPayment.objects.create(voucher=files.get('file'), insuree=insuree_obj)
        Notification.objects.create(insuree=insuree_obj, message="Your Submission has been saved thank you", chf_id=insuree)
        return CreateVoucherPaymentMutation(ok=True)
        # img = info.context.files[file].read()
    

class NoticeInput(graphene.InputObjectType):
    # id = graphene.Int(required=False)
    title = graphene.String(required=True)
    description = graphene.String(required=True)

class NoticeType(DjangoObjectType):
    class Meta:
        model = Notice
        fields = ['title', 'description']


class FeedbackAppGQLType(DjangoObjectType):
    class Meta:
        model = Feedback
        interfaces = (graphene.relay.Node,)
        filter_fields= {
            "fullname": ['exact', 'icontains', 'istartswith'],

        }

        connection_class = ExtendedConnection

class CreateFeedbackMutation(graphene.Mutation):
    class Arguments:
        fullname = graphene.String(required=True)
        email_address = graphene.String(required=True)
        mobile_number = graphene.String(required=True)
        queries = graphene.String(required=True)
    feedback= graphene.Field(FeedbackAppGQLType)

    @classmethod
    def mutate(cls,root,info, **kwargs):
        print(kwargs)
        feedback = Feedback.objects.create(**kwargs)
        return CreateFeedbackMutation(feedback=feedback)


class CreateNoticeMutation(OpenIMISMutation):#graphene.relay.ClientIDMutation):
    # _mutation_module = "webapp"
    # _mutation_class = "CreateNoticeMutation"
    class Input:
        title = graphene.String(required=True)
        description = graphene.String(required=True)
        client_mutation_id = graphene.String()
        client_mutation_label = graphene.String()

    notice = graphene.Field(NoticeType)
   
    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        print('CreateNoticeMutation mutate')
        data = input
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        print(input)
        notice = Notice.objects.create(title=input['title'], description=input['description'])
        return CreateNoticeMutation(notice=notice)


# class UpdateNoticeMutation(graphene.Mutation):
#     class Arguments:
#         id = graphene.Int(required=True)
#         title = graphene.String(required=False,)
#         description = graphene.String(required=False)
#     notice = graphene.Field(NoticeType)
    
#     def mutate(self, info,cls, **input):
#         try:
#             notice = Notice.objects.filter(pk=kwargs['id']).first()
#             notice.update(title=kwargs['title'], description=kwargs['description'])
#             return UpdateNoticeMutation(notice=notice)
#         except:
#             return GraphQLError('The notice you are updating might not exist anymore')

class UpdateNoticeMutation(OpenIMISMutation):
    notice = graphene.Field(NoticeType)

    class Input(OpenIMISMutation.Input):
        id = graphene.String()
        title = graphene.String(required=False,)
        description = graphene.String(required=True)
        client_mutation_id = graphene.String()
        client_mutation_label = graphene.String()
    
    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        dfprint('UpdateNoticeMutation mutate')
        data = input
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        try:
            notice = Notice.objects.filter(pk=fbis64(input['id'])) #;dfprint(notice)
            notice.update(title=input['title'], description=input['description'])
            return UpdateNoticeMutation(notice=notice)
        except:
            return GraphQLError('The notice you are updating might not exist anymore')

class DeleteNoticeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
    
    notice = graphene.Field(NoticeType)
    @classmethod
    def mutate(self, info, cls, id):
        try:
            notice = Notice.objects.filter(pk=id).first()
            notice.active = False #soft_delete
            notice.save()
            return DeleteNoticeMutation(notice=notice)
        except:
            return GraphQLError('The notice you are deleting might not exist anymore')


from .models import InsureeTempReg
import base64

from insuree.schema import  InsureeGQLType
class CreateTempRegInsureeMutation(graphene.Mutation):
    class Arguments:
        json = graphene.JSONString()
    ok = graphene.Boolean()
    @classmethod
    def mutate(self, info, cls, **kwargs):
        print(kwargs)
        InsureeTempReg.objects.create(json=kwargs['json'])
        return CreateTempRegInsureeMutation(ok=True)

import json

class CreateInsureeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.String()
    ok = graphene.Boolean()
    @classmethod
    def mutate(self, info, cls, **kwargs):
        photo = "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"
        temp_insuree = InsureeTempReg.objects.filter(pk=3).first()
        str_json = temp_insuree.json
        json_dict = json.loads(str_json)
        json_dict = { "ExistingInsuree": 
                { "CHFID": "200" }, "Family": { "LocationId": "", "Poverty": False, "FamilyType": "", "FamilyAddress": "", "isOffline": "", "Ethnicity": "", "ConfirmationNo": "", "ConfirmationType": "" }, "Insurees": [ { "LastName": "", "OtherNames": "", "DOB": "2020-01-01", "Gender": "", "Marital": "", "IsHead": "", "passport": "", "Phone": "", "LegacyID": "", "Relationship": "", "Profession": "", "Education": "", "Email": "", "CurrentAddress": "" } ] }
        family_save = json_dict.get("Family")
        insuree_save = json_dict.get("Insuree")

        try:
            # insuree_create["family_id"] = family.id
            #insuree = insuree_models.Insuree.objects.create(**insuree_create)
            print("saueko")
            # return CreateInsureeMutation(ok=True)
            chfid = None
            if json_dict.get("ExistingInsuree"):
                chfid = json_dict.get('ExistingInsuree').get('CHFID')
            if chfid:
                family_id = insuree_models.Insuree.objects.filter(chf_id=chfid).first().family.id
            else:
                insuree_ = insuree_models.Insuree.objects.all().first()
                family_create = {
                    "head_insuree_id" : 1,
                    #"location" : ""
                    #"family_type_id": None,
                    #"address": ,
                    #"ethnicity" : "noob",
                    "validity_from" : "2020-01-01",
                    "audit_user_id" : 1,

                }
                family_create["head_insuree_id"] = insuree_.id
                family =insuree_models.Family.objects.create(**family_create)
                family_id = family.id
            if family_id:
                insurees_from_form = json_dict.get("Insurees")
                for insuree_save in insurees_from_form:
                    insuree_create = {
                        "last_name" : insuree_save.get("LastName", None),
                        "other_names" : insuree_save.get("OtherNames", None),
                    # "gender_id": insuree_save.get("Gender", 1),
                        #"martial": insuree_save.get("Martial", None),
                        #"chf_id" : insuree_save.get("CHFID", None),
                        "dob" : insuree_save.get("DOB", "2000-01-01"),
                        "head" : True, #insuree_save.get("IsHead", False),
                        #"passport" : insuree_save.get("passport", None),
                        "validity_from" : "2020-01-01",
                        "card_issued" : False,
                        "audit_user_id": 1,
                    # "audit_user_id" : 1,

                    }
                    
                    insuree_create["family_id"] = family_id
                    insuree_models.Insuree.objects.create(**insuree_create)
                    save_path="/Users/abc"
                    image_data = base64.b64decode(photo) 

                    image_result = open('deer_decode.jpg', 'wb')

                    final_image = image_result.write(image_data)
                    print(final_image)



            # print(insuree_create)
            # insuree = insuree_models.Insuree.objects.create(**insuree_create)
        except Exception as e:
            print("jpob")
            print(e)
            import traceback
            traceback.print_exc()
            raise




        # insuree.save()
        return CreateInsureeMutation(ok=True)



# class CreateExistingInsuree(graphene.Mutation):
#     class Arguments:
#         chf_id = graphene.String()
#     ok = graphene.BooleanField()
#     @classmethod
#     def mutate(self, info, cls, **kwargs):






# class ClaimItemInputType(InputObjectType):
#     id = graphene.Int(required=False)
#     item_id = graphene.Int(required=True)
#     status = TinyInt(required=True)
#     qty_provided = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     qty_approved = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_asked = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_adjusted = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_approved = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_valuated = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     explanation = graphene.String(required=False)
#     justification = graphene.String(required=False)
#     rejection_reason = SmallInt(required=False)

#     validity_from_review = graphene.DateTime(required=False)
#     validity_to_review = graphene.DateTime(required=False)
#     limitation_value = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     limitation = graphene.String(required=False)
#     remunerated_amount = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     deductable_amount = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     exceed_ceiling_amount = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_origin = graphene.String(required=False)
#     exceed_ceiling_amount_category = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)


# class ClaimServiceInputType(InputObjectType):
#     id = graphene.Int(required=False)
#     legacy_id = graphene.Int(required=False)
#     service_id = graphene.Int(required=True)
#     status = TinyInt(required=True)
#     qty_provided = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     qty_approved = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_asked = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_adjusted = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_approved = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_valuated = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     explanation = graphene.String(required=False)
#     justification = graphene.String(required=False)
#     rejection_reason = SmallInt(required=False)
#     validity_to = graphene.DateTime(required=False)
#     validity_from_review = graphene.DateTime(required=False)
#     validity_to_review = graphene.DateTime(required=False)
#     audit_user_id_review = graphene.Int(required=False)
#     limitation_value = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     limitation = graphene.String(max_length=1, required=False)
#     policy_id = graphene.Int(required=False)
#     remunerated_amount = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     deductable_amount = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False,
#         description="deductable is spelled with a, not deductible")
#     exceed_ceiling_amount = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)
#     price_origin = graphene.String(max_length=1, required=False)
#     exceed_ceiling_amount_category = graphene.Decimal(
#         max_digits=18, decimal_places=2, required=False)


# class FeedbackInputType(InputObjectType):
#     id = graphene.Int(required=False, read_only=True)
#     care_rendered = graphene.Boolean(required=False)
#     payment_asked = graphene.Boolean(required=False)
#     drug_prescribed = graphene.Boolean(required=False)
#     drug_received = graphene.Boolean(required=False)
#     asessment = SmallInt(
#         required=False,
#         description="Be careful, this field name has a typo")
#     officer_id = graphene.Int(required=False)
#     feedback_date = graphene.DateTime(required=False)
#     validity_from = graphene.DateTime(required=False)
#     validity_to = graphene.DateTime(required=False)


# class ClaimCodeInputType(graphene.String):

#     @staticmethod
#     def coerce_string(value):
#         assert_string_length(value, 8)
#         return value

#     serialize = coerce_string
#     parse_value = coerce_string

#     @staticmethod
#     def parse_literal(ast):
#         result = graphene.String.parse_literal(ast)
#         assert_string_length(result, 8)
#         return result


# class ClaimGuaranteeIdInputType(graphene.String):

#     @staticmethod
#     def coerce_string(value):
#         assert_string_length(value, 50)
#         return value

#     serialize = coerce_string
#     parse_value = coerce_string

#     @staticmethod
#     def parse_literal(ast):
#         result = graphene.String.parse_literal(ast)
#         assert_string_length(result, 50)
#         return result


# class BaseAttachment:
#     id = graphene.String(required=False, read_only=True)
#     type = graphene.String(required=False)
#     title = graphene.String(required=False)
#     date = graphene.Date(required=False)
#     filename = graphene.String(required=False)
#     mime = graphene.String(required=False)
#     url = graphene.String(required=False)


# class BaseAttachmentInputType(BaseAttachment, OpenIMISMutation.Input):
#     """
#     Claim attachment (without the document), used on its own
#     """
#     claim_uuid = graphene.String(required=True)


# class Attachment(BaseAttachment):
#     document = graphene.String(required=False)


# class ClaimAttachmentInputType(Attachment, InputObjectType):
#     """
#     Claim attachment, used nested in claim object
#     """
#     pass


# class AttachmentInputType(Attachment, OpenIMISMutation.Input):
#     """
#     Claim attachment, used on its own
#     """
#     claim_uuid = graphene.String(required=True)


# class ClaimInputType(OpenIMISMutation.Input):
#     id = graphene.Int(required=False, read_only=True)
#     uuid = graphene.String(required=False)
#     code = ClaimCodeInputType(required=True)
#     insuree_id = graphene.Int(required=True)
#     date_from = graphene.Date(required=True)
#     date_to = graphene.Date(required=False)
#     icd_id = graphene.Int(required=True)
#     icd_1_id = graphene.Int(required=False)
#     icd_2_id = graphene.Int(required=False)
#     icd_3_id = graphene.Int(required=False)
#     icd_4_id = graphene.Int(required=False)
#     review_status = TinyInt(required=False)
#     date_claimed = graphene.Date(required=True)
#     date_processed = graphene.Date(required=False)
#     health_facility_id = graphene.Int(required=True)
#     batch_run_id = graphene.Int(required=False)
#     category = graphene.String(max_length=1, required=False)
#     visit_type = graphene.String(max_length=1, required=False)
#     admin_id = graphene.Int(required=False)
#     guarantee_id = ClaimGuaranteeIdInputType(required=False)
#     explanation = graphene.String(required=False)
#     adjustment = graphene.String(required=False)
#     json_ext = graphene.types.json.JSONString(required=False)

#     feedback_available = graphene.Boolean(default=False)
#     feedback_status = TinyInt(required=False)
#     feedback = graphene.Field(FeedbackInputType, required=False)

#     items = graphene.List(ClaimItemInputType, required=False)
#     services = graphene.List(ClaimServiceInputType, required=False)


# class CreateClaimInputType(ClaimInputType):
#     attachments = graphene.List(ClaimAttachmentInputType, required=False)


# def reset_claim_before_update(claim):
#     claim.date_to = None
#     claim.icd_1 = None
#     claim.icd_2 = None
#     claim.icd_3 = None
#     claim.icd_4 = None
#     claim.guarantee_id = None
#     claim.explanation = None
#     claim.adjustment = None
#     claim.json_ext = None


# def process_child_relation(user, data_children,
#                            claim_id, children, create_hook):
#     claimed = 0
#     from core.utils import TimeUtils
#     for data_elt in data_children:
#         claimed += data_elt['qty_provided'] * data_elt['price_asked']
#         elt_id = data_elt.pop('id') if 'id' in data_elt else None
#         if elt_id:
#             # elt has been historized along with claim historization
#             elt = children.get(id=elt_id)
#             [setattr(elt, k, v) for k, v in data_elt.items()]
#             elt.validity_from = TimeUtils.now()
#             elt.audit_user_id = user.id_for_audit
#             elt.claim_id = claim_id
#             elt.save()
#         else:
#             data_elt['validity_from'] = TimeUtils.now()
#             data_elt['audit_user_id'] = user.id_for_audit
#             create_hook(claim_id, data_elt)

#     return claimed


# def item_create_hook(claim_id, item):
#     # TODO: investigate 'availability' is mandatory,
#     # but not in UI > always true?
#     item['availability'] = True
#     ClaimItem.objects.create(claim_id=claim_id, **item)


# def service_create_hook(claim_id, service):
#     ClaimService.objects.create(claim_id=claim_id, **service)


# def create_file(date, claim_id, document):
#     date_iso = date.isoformat()
#     root = ClaimConfig.claim_attachments_root_path
#     file_dir = '%s/%s/%s/%s' % (
#         date_iso[0:4],
#         date_iso[5:7],
#         date_iso[8:10],
#         claim_id
#     )
#     file_path = '%s/%s' % (file_dir, uuid.uuid4())
#     pathlib.Path('%s/%s' % (root, file_dir)).mkdir(parents=True, exist_ok=True)
#     f = open('%s/%s' % (root, file_path), "xb")
#     f.write(base64.b64decode(document))
#     f.close()
#     return file_path


# def create_attachment(claim_id, data):
#     data["claim_id"] = claim_id
#     from core import datetime
#     now = datetime.datetime.now()
#     if ClaimConfig.claim_attachments_root_path:
#         # don't use data date as it may be updated by user afterwards!
#         data['url'] = create_file(now, claim_id, data.pop('document'))
#     data['validity_from'] = now
#     ClaimAttachment.objects.create(**data)


# def create_attachments(claim_id, attachments):
#     for attachment in attachments:
#         create_attachment(claim_id, attachment)


# def update_or_create_claim(data, user):
#     items = data.pop('items') if 'items' in data else []
#     services = data.pop('services') if 'services' in data else []
#     if "client_mutation_id" in data:
#         data.pop('client_mutation_id')
#     if "client_mutation_label" in data:
#         data.pop('client_mutation_label')
#     claim_uuid = data.pop('uuid') if 'uuid' in data else None
#     # update_or_create(uuid=claim_uuid, ...)
#     # doesn't work because of explicit attempt to set null to uuid!
#     prev_claim_id = None
#     if claim_uuid:
#         claim = Claim.objects.get(uuid=claim_uuid)
#         prev_claim_id = claim.save_history()
#         # reset the non required fields
#         # (each update is 'complete', necessary to be able to set 'null')
#         reset_claim_before_update(claim)
#         [setattr(claim, key, data[key]) for key in data]
#     else:
#         claim = Claim.objects.create(**data)
#     claimed = 0
#     claimed += process_child_relation(user, items,
#                                       claim.id, claim.items,
#                                       item_create_hook)
#     claimed += process_child_relation(user, services,
#                                       claim.id, claim.services,
#                                       service_create_hook)
#     claim.claimed = claimed
#     claim.save()
#     return claim


# class CreateClaimMutation(OpenIMISMutation):
#     """
#     Create a new claim. The claim items and services can all be entered with this call
#     """
#     _mutation_module = "claim"
#     _mutation_class = "CreateClaimMutation"

#     class Input(CreateClaimInputType):
#         pass

#     @classmethod
#     def async_mutate(cls, user, **data):
#         try:
#             # TODO move this verification to OIMutation
#             if type(user) is AnonymousUser or not user.id:
#                 raise ValidationError(
#                     _("mutation.authentication_required"))
#             if not user.has_perms(ClaimConfig.gql_mutation_create_claims_perms):
#                 raise PermissionDenied(_("unauthorized"))
#             # Claim code unicity should be enforced at DB Scheme level...
#             if Claim.objects.filter(code=data['code']).exists():
#                 return [{
#                     'message': _("claim.mutation.duplicated_claim_code") % {'code': data['code']},
#                 }]
#             data['audit_user_id'] = user.id_for_audit
#             data['status'] = Claim.STATUS_ENTERED
#             from core.utils import TimeUtils
#             data['validity_from'] = TimeUtils.now()
#             attachments = data.pop('attachments') if 'attachments' in data else None
#             claim = update_or_create_claim(data, user)
#             if attachments:
#                 create_attachments(claim.id, attachments)
#             return None
#         except Exception as exc:
#             return [{
#                 'message': _("claim.mutation.failed_to_create_claim") % {'code': data['code']},
#                 'detail': str(exc)}]


# class UpdateClaimMutation(OpenIMISMutation):
#     """
#     Update a claim. The claim items and services can all be updated with this call
#     """
#     _mutation_module = "claim"
#     _mutation_class = "UpdateClaimMutation"

#     class Input(ClaimInputType):
#         pass

#     @classmethod
#     def async_mutate(cls, user, **data):
#         try:
#             # TODO move this verification to OIMutation
#             if type(user) is AnonymousUser or not user.id:
#                 raise ValidationError(
#                     _("mutation.authentication_required"))
#             if not user.has_perms(ClaimConfig.gql_mutation_update_claims_perms):
#                 raise PermissionDenied(_("unauthorized"))
#             data['audit_user_id'] = user.id_for_audit
#             update_or_create_claim(data, user)
#             return None
#         except Exception as exc:
#             return [{
#                 'message': _("claim.mutation.failed_to_update_claim") % {'code': data['code']},
#                 'detail': str(exc)}]


# class CreateAttachmentMutation(OpenIMISMutation):
#     _mutation_module = "claim"
#     _mutation_class = "AddClaimAttachmentMutation"

#     class Input(AttachmentInputType):
#         pass

#     @classmethod
#     def async_mutate(cls, user, **data):
#         claim = None
#         try:
#             if user.is_anonymous or not user.has_perms(ClaimConfig.gql_mutation_update_claims_perms):
#                 raise PermissionDenied(_("unauthorized"))
#             if "client_mutation_id" in data:
#                 data.pop('client_mutation_id')
#             if "client_mutation_label" in data:
#                 data.pop('client_mutation_label')
#             claim_uuid = data.pop("claim_uuid")
#             queryset = Claim.objects.filter(*filter_validity())
#             if settings.ROW_SECURITY:
#                 dist = UserDistrict.get_user_districts(user._u)
#                 queryset = queryset.filter(
#                     health_facility__location__id__in=[
#                         l.location_id for l in dist]
#                 )
#             claim = queryset.filter(uuid=claim_uuid).first()
#             if not claim:
#                 raise PermissionDenied(_("unauthorized"))
#             create_attachment(claim.id, data)
#             return None
#         except Exception as exc:
#             return [{
#                 'message': _("claim.mutation.failed_to_attach_document") % {'code': claim.code if claim else None},
#                 'detail': str(exc)}]


# class UpdateAttachmentMutation(OpenIMISMutation):
#     _mutation_module = "claim"
#     _mutation_class = "UpdateAttachmentMutation"

#     class Input(BaseAttachmentInputType):
#         pass

#     @classmethod
#     def async_mutate(cls, user, **data):
#         try:
#             if not user.has_perms(ClaimConfig.gql_mutation_update_claims_perms):
#                 raise PermissionDenied(_("unauthorized"))
#             queryset = ClaimAttachment.objects.filter(*filter_validity())
#             if settings.ROW_SECURITY:
#                 from location.models import UserDistrict
#                 dist = UserDistrict.get_user_districts(user._u)
#                 queryset = queryset.select_related("claim") \
#                     .filter(
#                     claim__health_facility__location__id__in=[
#                         l.location_id for l in dist]
#                 )
#             attachment = queryset \
#                 .filter(id=data['id']) \
#                 .first()
#             if not attachment:
#                 raise PermissionDenied(_("unauthorized"))
#             attachment.save_history()
#             data['audit_user_id'] = user.id_for_audit
#             [setattr(attachment, key, data[key]) for key in data]
#             attachment.save()
#             return None
#         except Exception as exc:
#             return [{
#                 'message': _("claim.mutation.failed_to_update_claim_attachment") % {
#                     'code': attachment.claim.code,
#                     'filename': attachment.filename
#                 },
#                 'detail': str(exc)}]


# class DeleteAttachmentMutation(OpenIMISMutation):
#     _mutation_module = "claim"
#     _mutation_class = "DeleteClaimAttachmentMutation"

#     class Input(OpenIMISMutation.Input):
#         id = graphene.String()

#     @classmethod
#     def async_mutate(cls, user, **data):
#         try:
#             if not user.has_perms(ClaimConfig.gql_mutation_update_claims_perms):
#                 raise PermissionDenied(_("unauthorized"))
#             queryset = ClaimAttachment.objects.filter(*filter_validity())
#             if settings.ROW_SECURITY:
#                 from location.models import UserDistrict
#                 dist = UserDistrict.get_user_districts(user._u)
#                 queryset = queryset.select_related("claim") \
#                     .filter(
#                     claim__health_facility__location__id__in=[
#                         l.location_id for l in dist]
#                 )
#             attachment = queryset \
#                 .filter(id=data['id']) \
#                 .first()
#             if not attachment:
#                 raise PermissionDenied(_("unauthorized"))
#             attachment.delete_history()
#             return None
#         except Exception as exc:
#             return [{
#                 'message': _("claim.mutation.failed_to_delete_claim_attachment") % {
#                     'code': attachment.claim.code,
#                     'filename': attachment.filename
#                 },
#                 'detail': str(exc)}]


# class SubmitClaimsMutation(OpenIMISMutation):
#     """
#     Submit one or several claims.
#     """
#     __filter_handlers = {
#         'services': 'services__service__code__in',
#         'items': 'items__item__code__in'
#     }
#     _mutation_module = "claim"
#     _mutation_class = "SubmitClaimsMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)
#         additional_filters = graphene.String()

#     @classmethod
#     @mutation_on_uuids_from_filter(Claim, ClaimGQLType, 'additional_filters', __filter_handlers)
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_submit_claims_perms):
#             raise PermissionDenied(_("unauthorized"))
#         errors = []
#         uuids = data.get("uuids", [])

#         for claim_uuid in uuids:
#             c_errors = []
#             claim = Claim.objects \
#                 .filter(uuid=claim_uuid,
#                         validity_to__isnull=True) \
#                 .prefetch_related("items") \
#                 .prefetch_related("services") \
#                 .first()
#             if claim is None:
#                 errors += {
#                     'title': claim_uuid,
#                     'list': [
#                         {'message': _(
#                             "claim.validation.id_does_not_exist") % {'id': claim_uuid}}
#                     ]
#                 }
#                 continue
#             claim.save_history()
#             logger.debug("SubmitClaimsMutation: validating claim %s", claim_uuid)
#             c_errors += validate_claim(claim, True)
#             logger.debug("SubmitClaimsMutation: claim %s validated, nb of errors: %s", claim_uuid, len(c_errors))
#             if len(c_errors) == 0:
#                 c_errors = validate_assign_prod_to_claimitems_and_services(claim)
#                 logger.debug("SubmitClaimsMutation: claim %s assigned, nb of errors: %s", claim_uuid, len(c_errors))
#                 c_errors += process_dedrem(claim, user.id_for_audit, False)
#                 logger.debug("SubmitClaimsMutation: claim %s processed for dedrem, nb of errors: %s", claim_uuid,
#                              len(errors))
#             c_errors += set_claim_submitted(claim, c_errors, user)
#             logger.debug("SubmitClaimsMutation: claim %s set submitted", claim_uuid)
#             if c_errors:
#                 errors.append({
#                     'title': claim.code,
#                     'list': c_errors
#                 })
#         if len(errors) == 1:
#             errors = errors[0]['list']
#         logger.debug("SubmitClaimsMutation: claim done, errors: %s", len(errors))
#         return errors



# def set_claims_status(uuids, field, status, audit_data=None):
#     errors = []
#     for claim_uuid in uuids:
#         claim = Claim.objects \
#             .filter(uuid=claim_uuid,
#                     validity_to__isnull=True) \
#             .first()
#         if claim is None:
#             errors += [{'message': _(
#                 "claim.validation.id_does_not_exist") % {'id': claim_uuid}}]
#             continue
#         try:
#             claim.save_history()
#             setattr(claim, field, status)
#             if audit_data:
#                 for k, v in audit_data.items():
#                     setattr(claim, k, v)
#             claim.save()
#         except Exception as exc:
#             errors += [
#                 {'message': _("claim.mutation.failed_to_change_status_of_claim") %
#                             {'code': claim.code}}]

#     return errors


# def update_claims_dedrems(uuids, user):
#     # We could do it in one query with filter(claim__uuid__in=uuids) but we'd loose the logging
#     errors = []
#     for uuid in uuids:
#         logger.debug(f"delivering review on {uuid}, reprocessing dedrem ({user})")
#         claim = Claim.objects.get(uuid=uuid)
#         errors += validate_and_process_dedrem_claim(claim, user, False)
#     return errors


# class SelectClaimsForFeedbackMutation(OpenIMISMutation):
#     """
#     Select one or several claims for feedback.
#     """
#     _mutation_module = "claim"
#     _mutation_class = "SelectClaimsForFeedbackMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_select_claim_feedback_perms):
#             raise PermissionDenied(_("unauthorized"))
#         return set_claims_status(data['uuids'], 'feedback_status', Claim.FEEDBACK_SELECTED)


# class BypassClaimsFeedbackMutation(OpenIMISMutation):
#     """
#     Bypass feedback for one or several claims
#     """
#     _mutation_module = "claim"
#     _mutation_class = "BypassClaimsFeedbackMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_bypass_claim_feedback_perms):
#             raise PermissionDenied(_("unauthorized"))
#         return set_claims_status(data['uuids'], 'feedback_status', Claim.FEEDBACK_BYPASSED)


# class SkipClaimsFeedbackMutation(OpenIMISMutation):
#     """
#     Skip feedback for one or several claims
#     Skip indicates that the claim is not selected for feedback
#     """
#     _mutation_module = "claim"
#     _mutation_class = "SkipClaimsFeedbackMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_skip_claim_feedback_perms):
#             raise PermissionDenied(_("unauthorized"))
#         return set_claims_status(data['uuids'], 'feedback_status', Claim.FEEDBACK_NOT_SELECTED)


# class DeliverClaimFeedbackMutation(OpenIMISMutation):
#     """
#     Deliver feedback of a claim
#     """
#     _mutation_module = "claim"
#     _mutation_class = "DeliverClaimFeedbackMutation"

#     class Input(OpenIMISMutation.Input):
#         claim_uuid = graphene.String(required=False, read_only=True)
#         feedback = graphene.Field(FeedbackInputType, required=True)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         claim = None
#         try:
#             if not user.has_perms(ClaimConfig.gql_mutation_deliver_claim_feedback_perms):
#                 raise PermissionDenied(_("unauthorized"))
#             claim = Claim.objects.select_related('feedback').get(
#                 uuid=data['claim_uuid'],
#                 validity_to__isnull=True)
#             prev_feedback = claim.feedback
#             prev_claim_id = claim.save_history()
#             if prev_feedback:
#                 prev_feedback.claim_id = prev_claim_id
#                 prev_feedback.save()
#             feedback = data['feedback']
#             from core.utils import TimeUtils
#             feedback['validity_from'] = TimeUtils.now()
#             feedback['audit_user_id'] = user.id_for_audit
#             # The legacy model has a Foreign key on both sides of this one-to-one relationship
#             f, created = Feedback.objects.update_or_create(
#                 claim=claim,
#                 defaults=feedback
#             )
#             claim.feedback = f
#             claim.feedback_status = Claim.FEEDBACK_DELIVERED
#             claim.feedback_available = True
#             claim.save()
#             return None
#         except Exception as exc:
#             return [{
#                 'message': _("claim.mutation.failed_to_update_claim") % {'code': claim.code if claim else None},
#                 'detail': str(exc)}]


# class SelectClaimsForReviewMutation(OpenIMISMutation):
#     """
#     Select one or several claims for review.
#     """
#     _mutation_module = "claim"
#     _mutation_class = "SelectClaimsForReviewMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_select_claim_review_perms):
#             raise PermissionDenied(_("unauthorized"))
#         return set_claims_status(data['uuids'], 'review_status', Claim.REVIEW_SELECTED)


# class BypassClaimsReviewMutation(OpenIMISMutation):
#     """
#     Bypass review for one or several claims
#     Bypass indicates that review of a previously selected claim won't be delivered
#     """
#     _mutation_module = "claim"
#     _mutation_class = "BypassClaimsReviewMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_bypass_claim_review_perms):
#             raise PermissionDenied(_("unauthorized"))
#         return set_claims_status(data['uuids'], 'review_status', Claim.REVIEW_BYPASSED)


# class DeliverClaimsReviewMutation(OpenIMISMutation):
#     """
#     Mark claim review as delivered for one or several claims
#     """
#     _mutation_module = "claim"
#     _mutation_class = "DeliverClaimsReviewMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         logger.error("SaveClaimReviewMutation")
#         if not user.has_perms(ClaimConfig.gql_mutation_deliver_claim_review_perms):
#             raise PermissionDenied(_("unauthorized"))
#         errors = set_claims_status(data['uuids'], 'review_status', Claim.REVIEW_DELIVERED,
#                                    {'audit_user_id_review': user.id_for_audit})
#         # OMT-208 update the dedrem for the reviewed claims
#         errors += update_claims_dedrems(data["uuids"], user)

#         return errors


# class SkipClaimsReviewMutation(OpenIMISMutation):
#     """
#     Skip review for one or several claims
#     Skip indicates that the claim is not selected for review
#     """
#     _mutation_module = "claim"
#     _mutation_class = "SkipClaimsReviewMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_skip_claim_review_perms):
#             raise PermissionDenied(_("unauthorized"))
#         return set_claims_status(data['uuids'], 'review_status', Claim.REVIEW_NOT_SELECTED)


# class SaveClaimReviewMutation(OpenIMISMutation):
#     """
#     Save the review of a claim (items and services)
#     """
#     _mutation_module = "claim"
#     _mutation_class = "SaveClaimReviewMutation"

#     class Input(OpenIMISMutation.Input):
#         claim_uuid = graphene.String(required=False, read_only=True)
#         adjustment = graphene.String(required=False)
#         items = graphene.List(ClaimItemInputType, required=False)
#         services = graphene.List(ClaimServiceInputType, required=False)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         claim = None
#         try:
#             if not user.has_perms(ClaimConfig.gql_mutation_deliver_claim_review_perms):
#                 raise PermissionDenied(_("unauthorized"))
#             claim = Claim.objects.get(uuid=data['claim_uuid'],
#                                       validity_to__isnull=True)
#             if claim is None:
#                 return [{'message': _(
#                     "claim.validation.id_does_not_exist") % {'id': data['claim_uuid']}}]
#             claim.save_history()
#             claim.adjustment = data.get('adjustment', None)
#             items = data.pop('items') if 'items' in data else []
#             all_rejected = True
#             for item in items:
#                 item_id = item.pop('id')
#                 claim.items.filter(id=item_id).update(**item)
#                 if item['status'] == ClaimItem.STATUS_PASSED:
#                     all_rejected = False
#             services = data.pop('services') if 'services' in data else []
#             for service in services:
#                 service_id = service.pop('id')
#                 claim.services.filter(id=service_id).update(**service)
#                 if service['status'] == ClaimService.STATUS_PASSED:
#                     all_rejected = False
#             claim.approved = approved_amount(claim)
#             claim.audit_user_id_review = user.id_for_audit
#             if all_rejected:
#                 claim.status = Claim.STATUS_REJECTED
#             claim.save()
#             return None
#         except Exception as exc:
#             return [{
#                 'message': _("claim.mutation.failed_to_update_claim") % {'code': claim.code if claim else None},
#                 'detail': str(exc)}]


# class ProcessClaimsMutation(OpenIMISMutation):
#     """
#     Process one or several claims.
#     """
#     _mutation_module = "claim"
#     _mutation_class = "ProcessClaimsMutation"

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_process_claims_perms):
#             raise PermissionDenied(_("unauthorized"))
#         errors = []
#         for claim_uuid in data["uuids"]:
#             logger.debug("ProcessClaimsMutation: processing %s", claim_uuid)
#             c_errors = []
#             claim = Claim.objects \
#                 .filter(uuid=claim_uuid) \
#                 .prefetch_related("items") \
#                 .prefetch_related("services") \
#                 .first()
#             if claim is None:
#                 errors += {
#                     'title': claim_uuid,
#                     'list': [{'message': _(
#                         "claim.validation.id_does_not_exist") % {'id': claim_uuid}}]
#                 }
#                 continue
#             claim.save_history()
#             claim.audit_user_id_process = user.id_for_audit
#             logger.debug("ProcessClaimsMutation: validating claim %s", claim_uuid)
#             c_errors += validate_and_process_dedrem_claim(claim, user, True)

#             logger.debug("ProcessClaimsMutation: claim %s set processed or valuated", claim_uuid)
#             if c_errors:
#                 errors.append({
#                     'title': claim.code,
#                     'list': c_errors
#                 })

#         if len(errors) == 1:
#             errors = errors[0]['list']
#         logger.debug("ProcessClaimsMutation: claims %s done, errors: %s", data["uuids"], len(errors))
#         return errors


# class DeleteClaimsMutation(OpenIMISMutation):
#     """
#     Mark one or several claims as Deleted (validity_to)
#     """

#     class Input(OpenIMISMutation.Input):
#         uuids = graphene.List(graphene.String)

#     _mutation_module = "claim"
#     _mutation_class = "DeleteClaimsMutation"

#     @classmethod
#     def async_mutate(cls, user, **data):
#         if not user.has_perms(ClaimConfig.gql_mutation_delete_claims_perms):
#             raise PermissionDenied(_("unauthorized"))
#         errors = []
#         for claim_uuid in data["uuids"]:
#             claim = Claim.objects \
#                 .filter(uuid=claim_uuid) \
#                 .prefetch_related("items") \
#                 .prefetch_related("services") \
#                 .first()
#             if claim is None:
#                 errors += {
#                     'title': claim_uuid,
#                     'list': [{'message': _(
#                         "claim.validation.id_does_not_exist") % {'id': claim_uuid}}]
#                 }
#                 continue
#             errors += set_claim_deleted(claim)
#         if len(errors) == 1:
#             errors = errors[0]['list']
#         return errors


# def set_claim_submitted(claim, errors, user):
#     try:
#         claim.audit_user_id_submit = user.id_for_audit
#         if errors:
#             claim.status = Claim.STATUS_REJECTED
#         else:
#             claim.approved = approved_amount(claim)
#             claim.status = Claim.STATUS_CHECKED
#             from core.utils import TimeUtils
#             claim.submit_stamp = TimeUtils.now()
#             claim.category = get_claim_category(claim)
#         claim.save()
#         return []
#     except Exception as exc:
#         return {
#             'title': claim.code,
#             'list': [{
#                 'message': _("claim.mutation.failed_to_change_status_of_claim") % {'code': claim.code},
#                 'detail': claim.uuid}]
#         }


# def set_claim_deleted(claim):
#     try:
#         claim.delete_history()
#         return []
#     except Exception as exc:
#         return {
#             'title': claim.code,
#             'list': [{
#                 'message': _("claim.mutation.failed_to_change_status_of_claim") % {'code': claim.code},
#                 'detail': claim.uuid}]
#         }


# def details_with_relative_prices(details):
#     return details.filter(status=ClaimDetail.STATUS_PASSED) \
#         .filter(price_origin=ProductItemOrService.ORIGIN_RELATIVE) \
#         .exists()


# def with_relative_prices(claim):
#     return details_with_relative_prices(claim.items) or details_with_relative_prices(claim.services)


# def set_claim_processed_or_valuated(claim, errors, user):
#     try:
#         if errors:
#             claim.status = Claim.STATUS_REJECTED
#         else:
#             claim.status = Claim.STATUS_PROCESSED if with_relative_prices(claim) else Claim.STATUS_VALUATED
#             claim.audit_user_id_process = user.id_for_audit
#             from core.utils import TimeUtils
#             claim.process_stamp = TimeUtils.now()
#         claim.save()
#         return []
#     except Exception as ex:
#         return {
#             'title': claim.code,
#             'list': [{'message': _("claim.mutation.failed_to_change_status_of_claim") % {'code': claim.code},
#                       'detail': claim.uuid}]
#         }


# def validate_and_process_dedrem_claim(claim, user, is_process):
#     errors = validate_claim(claim, False)
#     logger.debug("ProcessClaimsMutation: claim %s validated, nb of errors: %s", claim.uuid, len(errors))
#     if len(errors) == 0:
#         errors = validate_assign_prod_to_claimitems_and_services(claim)
#         logger.debug("ProcessClaimsMutation: claim %s assigned, nb of errors: %s", claim.uuid, len(errors))
#         errors += process_dedrem(claim, user.id_for_audit, is_process)
#         logger.debug("ProcessClaimsMutation: claim %s processed for dedrem, nb of errors: %s", claim.uuid,
#                      len(errors))
#     else:
#         # OMT-208 the claim is invalid. If there is a dedrem, we need to clear it (caused by a review)
#         deleted_dedrems = ClaimDedRem.objects.filter(claim=claim).delete()
#         if deleted_dedrems:
#             logger.debug(f"Claim {claim.uuid} is invalid, we deleted its dedrem ({deleted_dedrems})")
#     if is_process:
#         errors += set_claim_processed_or_valuated(claim, errors, user)
#     return errors
