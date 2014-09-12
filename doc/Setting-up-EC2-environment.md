#*The project does not support this feature anymore*

Some calls, like vm provision, use the ec2 api. In order to have the api fully functional in your system, you must acomplish a few steps.

# Environment variables

Export the following variables in yout ~/.bash_profile or ~/.profile file.

export EC2_ACCESS_KEY=[YOUR EC2 ACCESS KEY]<br/>
export EC2_SECRET_KEY=[YOUR EC2 SECRET KEY]<br/>
export EC2_URL=[AN EC2 API ENDPOINT]<br/>
export EC2_SUBNET_ID=[SUBNET ID]<br/>
<br/>
Usually the EC2_SUBNET_ID variable is in the form [ALPHANUMERIC]-[ID]. Example: abc-1234

# Boto

Since we are using boto, if your ec2 api endpoint is not behind a https connection you need to create the file .boto in your home directory with the following content

    [Boto]
    #debug = 2
    num_retries = 2
    https_validate_certificates = false
