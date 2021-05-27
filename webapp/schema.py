import django
import uuid 
import graphene
from insuree import models as insuree_models
from claim import models as claim_models
from graphene_django import DjangoObjectType
from .models import InsureeAuth
# We do need all queries and mutations in the namespace here.
# from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutations import *  # lgtm [py/polluting-import]


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
    class Meta:
        model = InsureeAuth
        fields = ['id', 'token']

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
        fields = ['id', 'insuree_policies', 'insuree_claim']
    
    insuree_claim = graphene.List(InsureeClaimGQLType)
    insuree_policies = graphene.List(InsureePolicyType)
    def resolve_photos(value_obj,info):
        return value_obj.photos.all
    
    def resolve_insuree_policies(value_obj, info):
        return value_obj.insuree_policies.all()
    def resolve_insuree_claim(value_obj, info):
        # return value_obj.insuree.all()
        return claim_models.Claim.objects.filter(insuree=value_obj)



class Query(graphene.ObjectType):
    password = graphene.String()
    insuree_auth = graphene.Field(InsureeAuthGQLType, insureeCHFID=graphene.String(), familyHeadCHFID=graphene.String(), dob=graphene.Date())
    insuree_profile = graphene.Field(InsureeProfileGQLType, insureeCHFID=graphene.Int())

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
               insuree_auth_obj.save()
        return insuree_auth_obj
    
    def resolve_insuree_profile(self, info, insureeID,**kwargs):
        return insuree_models.Insuree.objects.get(id=insureeID)

        # if insuree_obj:
        #     return InsureeVerifyGQLType(insuree_obj)
        # return ''

    def generate_token(self):
        token = uuid.uuid4().hex[:6].upper()
        return token




class Mutation(graphene.ObjectType):
    
    create_notice = CreateNoticeMutation.Field()
    # update_claim = UpdateClaimMutation.Field()
    # create_claim_attachment = CreateAttachmentMutation.Field()
    # update_claim_attachment = UpdateAttachmentMutation.Field()
    # delete_claim_attachment = DeleteAttachmentMutation.Field()




