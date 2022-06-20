# Setting up your CodeBuild Service Role

See this document on how to create a service role to be used by codebuild:

https://docs.aws.amazon.com/codebuild/latest/userguide/setting-up.html#setting-up-service-role

Then allow to access SSM Parameters

`aws iam attach-role-policy --role-name CodeBuildServiceRole --policy-arn arn:aws:iam::827659017777:policy/SSMGetParameters`


In case the policy is not available:
```
{
    "Version": "2012-10-17",
    "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameters"
                ],
                "Resource": "*"
            }
        ]
    },
    "VersionId": "v1",
    "IsDefaultVersion": true,
    "CreateDate": "2019-06-16T16:34:07Z"
}
```
