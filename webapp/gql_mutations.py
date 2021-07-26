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
    if not inp:
        return inp
    dfprint('fbis64')
    # NoticeGQLType:38
    # 
    bstr = base64.b64decode(inp)
    sstr = bstr.decode('utf-8')
    istrs = sstr.split(':')
    istr = istrs[1]
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
from .models import Notice, VoucherPayment, Feedback, Config
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
        insureeCHFID = graphene.String()  # basically chfid
        email = graphene.String()
        phone = graphene.String()

    ok = graphene.Boolean()

    # @classmethod
    def mutate(self, info, file, insureeCHFID, email, phone):
        files = info.context.FILES
        print(files)
        insuree_obj = insuree_models.Insuree.objects.filter(chf_id=insureeCHFID).first()
        print(insuree_obj.pk)
        instance = Profile.objects.filter(insuree_id=insuree_obj.pk).first()
        if not instance:
            instance = Profile()
        instance.photo = files.get('file') if files.get('file') else instance.photo
        instance.email = email if email else instance.email
        instance.phone = phone if phone else instance.phone
        instance.save()
        return CreateOrUpdateProfileMutation(ok=True)


from .models import Notification


class CreateVoucherPaymentMutation(graphene.Mutation):
    # _mutation_module = "webapp"
    # _mutation_class = "CreateNoticeMutation"
    class Arguments(object):
        file = graphene.List(graphene.String)
        insuree = graphene.String()

    ok = graphene.Boolean()

    # @classmethod
    def mutate(self, info, file, insuree):
        files = info.context.FILES
        # print(info.context)
        insuree_obj = insuree_models.Insuree.objects.filter(chf_id=insuree).first()
        VoucherPayment.objects.create(voucher=files.get('file'), insuree=insuree_obj)
        Notification.objects.create(insuree=insuree_obj, message="Your Submission has been saved thank you",
                                    chf_id=insuree)
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
        filter_fields = {
            "fullname": ['exact', 'icontains', 'istartswith'],

        }

        connection_class = ExtendedConnection


class CreateFeedbackMutation(graphene.Mutation):
    class Arguments:
        fullname = graphene.String(required=True)
        email_address = graphene.String(required=True)
        mobile_number = graphene.String(required=True)
        queries = graphene.String(required=True)

    feedback = graphene.Field(FeedbackAppGQLType)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        print(kwargs)
        feedback = Feedback.objects.create(**kwargs)
        return CreateFeedbackMutation(feedback=feedback)


class CreateNoticeMutation(OpenIMISMutation):  # graphene.relay.ClientIDMutation):
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


class UpdateNoticeMutation(OpenIMISMutation):
    notice = graphene.Field(NoticeType)

    class Input(OpenIMISMutation.Input):
        id = graphene.String()
        title = graphene.String(required=False, )
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
            notice = Notice.objects.filter(pk=fbis64(input['id']))  # ;dfprint(notice)
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
            notice.active = False  # soft_delete
            notice.save()
            return DeleteNoticeMutation(notice=notice)
        except:
            return GraphQLError('The notice you are deleting might not exist anymore')


from .models import InsureeTempReg
import base64

from insuree.schema import InsureeGQLType


class CreateTempRegInsureeMutation(graphene.Mutation):
    class Arguments:
        json = graphene.JSONString()
    ok = graphene.Boolean()

    @classmethod
    def mutate(self, info, cls, **kwargs):
        dfprint(kwargs)
        inp_json = kwargs['json']
        str_json = json.dumps(inp_json)  # stringify json to save imp_json.get("Isurees"]
        dfprint(str_json)
        jantu = inp_json.get("Insurees")[0]
        phone_number=jantu.get("Phone")
        
        tempReg=None
        tempReg=InsureeTempReg.objects.filter(phone_number=phone_number).first()
        if tempReg:
            tempReg.json = str_json
        else:
            tempReg = InsureeTempReg.objects.create(json=str_json)
        tempReg.name_of_head=jantu.get("OtherNames") + ' ' + jantu.get("LastName"),
        tempReg.phone_number=phone_number
        tempReg.save()

        return CreateTempRegInsureeMutation(ok=True)


import json


def mdlInsureePhoto():
    mdl = None
    if 'Photo' in dir(insuree_models): mdl = insuree_models.Photo
    if not mdl: mdl = insuree_models.InsureePhoto
    return mdl


def dbg_tmp_insuree_json():
    return {
        "ExistingInsuree": {"CHFID": "200"},
        "Family": {"LocationId": "", "Poverty": False, "FamilyType": "", "FamilyAddress": "", "isOffline": "",
                   "Ethnicity": "", "ConfirmationNo": "", "ConfirmationType": ""},
        "Insurees": [{"LastName": "", "OtherNames": "", "DOB": "2020-01-01", "Gender": "", "Marital": "", "IsHead": "",
                      "passport": "", "Phone": "", "LegacyID": "", "Relationship": "", "Profession": "",
                      "Education": "", "Email": "", "CurrentAddress": ""}]
    }


def dbg_tmp_insuree_photo():
    # 16x16 jpg img
    return "9j/4AAQSkZJRgABAQEAYABgAAD/4QA4RXhpZgAATU0AKgAAAAgAAgESAAMAAAABAAEAAAExAAIAAAAKAAAAJgAAAABHcmVlbnNob3QA/9sAQwACAQECAQECAgICAgICAgMFAwMDAwMGBAQDBQcGBwcHBgcHCAkLCQgICggHBwoNCgoLDAwMDAcJDg8NDA4LDAwM/9sAQwECAgIDAwMGAwMGDAgHCAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwM/8AAEQgAEAAQAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/aAAwDAQACEQMRAD8A8V/Zu+B/is663xY8P29veab4b8XTX1xcXSmSz0S4tdQDpLPDkPJG22EP5SyfI+CAwGL37Vf7Efibw3bR6vJ4U0/wq2tztc2NjaTXOpRFPKaWRBctJIwbgYVgS245YBGaqn7GH/BRyT4VQeO/hX4k8drofh29stfXQNQN1aRyeFdQd55cr5sTs0c0g2GMEMGk3LgncNv/AIKAf8FI9H+Mn7Pfww0yx8YaXd+KbaC8tfFBtdUS4t726ZYI2vngAWFZZRHMVdUKhJWCnJOPn8zzzNIRVDCtWtyWabum7q+trRbvom079z6zJ45ZzcuNh5tp2ei2Xdvb/I//2Q=="


def process_family(args):
    json_dict = args.get('json_dict')
    family_save = json_dict.get("Family")

    chfid = None
    family_id = None
    if json_dict.get("ExistingInsuree"):
        chfid = json_dict.get('ExistingInsuree').get('CHFID')
        family = insuree_models.Insuree.objects.filter(chf_id=chfid).first()
        if family:
            family_id = family.family.id
    if not family_id:
        print('familty-dict', insuree_models.Family().__dict__)
        print('family-save', family_save)
        insuree_ = insuree_models.Insuree.objects.all().first()
        family_create = {
            "head_insuree_id": insuree_.pk,
            # "location_id" : 1,
            "poverty": family_save.get('Poverty', False),
            "family_type_id": family_save.get('FamilyType', "C"),
            "address": family_save.get("FamilyAddress"),
            "ethnicity": family_save.get("Ethnicity"),
            "validity_from": "2020-01-01",
            "audit_user_id": 1,
            "is_offline": True,
            # "confirmation_no" : None,
            # "confirmation_type_id": None,

        }
        family_create["head_insuree_id"] = insuree_.id
        print('familty-save-after', family_create)
        family = insuree_models.Family.objects.create(**family_create)
        family_id = family.id
    return family_id

def process_b64photo_write(args):
    dfprint('process_b64photo_write')
    photo = args.get('b64photo')
    save_path=args.get('save_path')
    img_name=""
    if photo:
        img_type, img = photo.split(',')
        image_data = base64.b64decode(img)

        s = img_type  # 'data:image/jpeg;base64'
        img_name = s[5:s.index(';')].replace('/', '.')
        import time;
        img_name = str(time.time()) + img_name
        import os 
        os.makedirs(save_path, exist_ok=True)
        img_fullpath=os.path.join(save_path, img_name)
        image_result = open(img_fullpath, 'wb')
        final_image = image_result.write(image_data)
    return img_name

def process_photo(args):
    dfprint('process_photo')
    insuree_save = args.get('insuree_save')
    photo = insuree_save.get('B64Photo')  # dbg_tmp_insuree_photo()
    # print( insuree_models.__dict__ )

    save_path=""
    img_name=""
    if photo:  # and False:        
        cfg = Config.objects.filter(key='InsureeImageDir').first()
        if cfg:
            save_path = cfg.value
        img_name=process_b64photo_write({"b64photo": photo, "save_path":save_path})

    
    modelPhoto = mdlInsureePhoto().objects.create(**{
        # "insuree_id":insuree_save.get('InsureeId'),
        "folder": save_path,
        "filename": img_name,
        "officer_id": 3,  # todo
        "date": '2018-03-28',  # todo
        "validity_from": "2018-03-28",
    })

    cfg = Config.objects.filter(key='IdImageDir').first()
    process_b64photo_write({"b64photo":  insuree_save.get('B64IdPhoto'), "save_path":cfg.value})

    return modelPhoto.pk


def process_insuree(args):
    insuree_save = args.get('insuree_save')
    family_id = args.get('family_id')
    dob = insuree_save.get("DOB", )
    dob = dob if len(dob) == 10 else "2022-02-02"  # todo fix
    photo_id = args.get('photo_id')
    insuree_create = {
        "last_name": insuree_save.get("LastName", None),
        "other_names": insuree_save.get("OtherNames", None),
        "dob": insuree_save.get("DOB"),
        "gender_id": insuree_save.get("Gender"),
        "marital": insuree_save.get("Marital"),
        "head": insuree_save.get("IsHead") if insuree_save.get('IsHead') else False,
        "passport": insuree_save.get("passport", 0),
        "phone": insuree_save.get("Phone"),
        "email": insuree_save.get("Email"),
        "relationship_id": insuree_save.get("Relationship"),
        "education_id": insuree_save.get("Education"),
        "current_address": insuree_save.get("CurrentAddress"),
        "current_village_id": fbis64(insuree_save.get("VillId")),  # base64
        "profession_id": insuree_save.get("Profession"),
        # "validity_from" : "2020-01-01",
        "card_issued": False,
        "audit_user_id": 1,
        'photo_id': photo_id,
        # "audit_user_id" : 1,
    }
    insuree_create["family_id"] = family_id
    dfprint(insuree_create)
    modelInsuree = insuree_models.Insuree.objects.create(**insuree_create)
    return modelInsuree.pk
    pass


"""
mutation {
  createInsureeMutationFromTemp(id:"7"){
      ok
  }
}

SELECT TOP 10 * FROM tblInsuree ORDER BY insureeId DESC;
SELECT TOP 10 * FROM tblPhotos ORDER BY PhotoId DESC;
sp_help tblPhotos
"""
from .models import ChfidTempInsuree


class CreateInsureeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.String()
        is_hold = graphene.Boolean()
        is_rejected = graphene.Boolean()
        is_approved = graphene.Boolean()
        status_message = graphene.String()

    ok = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(self, info, cls, **kwargs):
        dfprint('CreateInsureeMutation mutate')
        message = ""
        try:
            pk = kwargs['id']  # access Arguments #13 testing
            temp_insuree = InsureeTempReg.objects.filter(pk=pk).first()
            print('kwargs----------',kwargs)
            if kwargs.get('is_hold'):
                temp_insuree.is_hold = True
                temp_insuree.status_message = kwargs.get('status_message')
                temp_insuree.save()
            if kwargs.get('is_rejected'):
                temp_insuree.is_rejected = True
                temp_insuree.status_message = kwargs.get('status_message')
                temp_insuree.save()
            if kwargs.get('is_hold'):
                temp_insuree.is_hold = True
                temp_insuree.status_message = kwargs.get('status_message')
                temp_insuree.save()
            if kwargs.get("is_approved"):
                
                str_json = temp_insuree.json
                json_dict = json.loads(str_json)  # dbg_tmp_insuree_json()
                family_id = process_family({'json_dict': json_dict})
                
                cfg = Config.objects.filter(key='RegVoucherImageDir').first()
                process_b64photo_write({"b64photo": json_dict.get('B64VoucherPhoto'), "save_path":cfg.value})

                if family_id:
                    insurees_from_form = json_dict.get("Insurees")
                    for insuree_save in insurees_from_form:
                        photo_id = process_photo({'insuree_save': insuree_save})
                        insuree_id = process_insuree(
                            {'insuree_save': insuree_save, 'photo_id': photo_id, 'family_id': family_id})
                        mdlInsureePhoto().objects.filter(pk=photo_id).update(**{"insuree_id": insuree_id})
                        chfif_assign = ChfidTempInsuree.objects.filter(is_approved=False).first()
                        if not chfif_assign:
                            message = "No CHFID available in database"
                        else:
                            chfif_assign.is_approved = True
                            # chfif_assign.save()
                            insuree_models.Insuree.objects.filter(pk=insuree_id).update(**{"chf_id": chfif_assign.chfid})
                            temp_insuree.is_approved = True
                            temp_insuree.save()

                    # everything ok, then approved flag changed
                    temp_insuree.is_approved = True
                    temp_insuree.status_message = kwargs.get('statusMessage')
                    temp_insuree.save()
        except Exception as e:
            print(e)
            import traceback
            traceback.print_exc()
            return CreateInsureeMutation(ok=False, message=message)
            # raise
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
