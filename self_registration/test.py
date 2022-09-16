import json
a = '{"Insuree": {"InsureeID": 11112222, "InsureeUUID": 12121212121212120, "FamilyID": 33311111, "CHFID": 2121212121, "LastName": "terobaje", "OtherNames": "hamrobaje", "DOB": "2021-01-01", "Gender": "male", "Marital": "", "IsHead": "True", "passport": "", "Phone": "", "PhotoID": "", "PhotoDate": "", "CardIssued": "", "ValidityFrom": "", "ValidityTo": "", "LegacyID": 1, "AuditUserID": "", "RowID": "", "Relationship": "", "Profession": "", "Education": "", "Email": "", "isOffline": "", "TypeOfId": "", "HFID": "", "CurrentAddress": "", "Geolocation": "", "CurrentVillage": ""}, "Family": {"FamilyID": "", "FamilyUUID": "", "InsureeID": "", "LocationId": "", "Poverty": "", "ValidityFrom": "", "ValidityTo": "", "LegacyID": 1, "AuditUserID": "", "RowID": "", "FamilyType": "", "FamilyAddress": "", "isOffline": "", "Ethnicity": "", "ConfirmationNo": "", "ConfirmationType": ""}}'

v = json.loads(a)
print(v["Insuree"])

