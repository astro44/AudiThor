AudiThor Service Auditor!
=========================

![Audithor hammer](AudiThor/img/hammer.png)
QuikStart:

 1. Run requirements.txt to install requirements via pip (inside a venv to keep it small).
 2. Modify CONFIG.yaml to suite your needs.
 3. zip requirements and code and upload into your lambda.
 4. Ensure that the Lambda role has permission to write to given bucket. 

SUMMARY:
Audithor was intended to be used as an auditor for your AWS accounts. It currently supports EC2, RDS, Lambda, Dynamodb, S3, ELB, and more.  The outputs are in CSV and JSON  format.  There also is an out specifically tailored for SumoLogic, In this case you can achieve nice dashboards with little effort.

----------


#### <i class="icon-file"></i>CONFIG
-------------

Configuration is stored in a yaml file CONFIG.yaml and contains general config under  the following keys:

> **auditConfig:**

> - **main_bucket** used to aggregate data about target accounts.
> -  **method**  name of the method created to use this application within your lambda service.
> - **key** you can leave this. (*its used to dynamically flag '%s' initialized process on account id)
> - **key_complete** you can leave this. (*its used to dynamically store result data based on account id)
> - **key_master** you can leave this. (*Stores all accounts for later reference)
> - **key_folder** you can leave this. (*Directory where all above files are stored during processing)
> - **thread_event** you can leave this. (*Lambda's have 5min limits keeping this to type "Event" helps mitigate the possible timeout)
> - **threaded** you can leave this. (*Lambda functions currently do not allow multi-processing which is why this is set to True)
> - **region** set to the target region.
> - **vendor** name of your organization
> - **sumo_file** you can leave this. (*name of the file generated before sending to sumoLogic)


> **globalAccounts:**

> - **Account#** references the unique AWS ID for said account.
>> -  **all**  short name used to reference said account.
>> - **title** Display name used to reference said account.
>> - **eID** external ID used in IAM role to allow trusted access from alternate account.
>> - **role** role created for this account that incoming role/user can assume using above eID.



