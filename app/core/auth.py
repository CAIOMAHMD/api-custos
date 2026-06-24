from azure.identity import InteractiveBrowserCredential

TENANT_ID = "f1ec76ca-ef9b-4758-8367-4ce8323c45ed"

credential = InteractiveBrowserCredential(
    tenant_id=TENANT_ID
)

def get_token():
    token = credential.get_token("https://management.azure.com/.default")
    return token.token
