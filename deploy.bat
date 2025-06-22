@echo off

set BUCKET_NAME=nextstep123
set DATABASE_URL=DATABASE_URL=postgresql://postgres:july252003@database-3.cluster-cbyqss0wi0ta.eu-north-1.rds.amazonaws.com:5432/nextstepdb
set OPENAI_API_KEY=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
set REGION=us-east-1
set KEY_NAME=nsf-ai-key
set INSTANCE_TYPE=t3.medium
set SECURITY_GROUP_NAME=nsf-ai-sg

for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set AWS_ACCOUNT_ID=%%i

aws ec2 create-key-pair --key-name %KEY_NAME% --query 'KeyMaterial' --output text --region %REGION% > %KEY_NAME%.pem
powershell -Command "icacls '%KEY_NAME%.pem' /inheritance:r /grant:r '%USERNAME%:(R)'"

aws ec2 create-security-group --group-name %SECURITY_GROUP_NAME% --description "NSF AI App Security Group" --region %REGION%

for /f "tokens=*" %%i in ('aws ec2 describe-security-groups --group-names %SECURITY_GROUP_NAME% --query "SecurityGroups[0].GroupId" --output text --region %REGION%') do set SECURITY_GROUP_ID=%%i

aws ec2 authorize-security-group-ingress --group-id %SECURITY_GROUP_ID% --protocol tcp --port 22 --cidr 0.0.0.0/0 --region %REGION%
aws ec2 authorize-security-group-ingress --group-id %SECURITY_GROUP_ID% --protocol tcp --port 80 --cidr 0.0.0.0/0 --region %REGION%
aws ec2 authorize-security-group-ingress --group-id %SECURITY_GROUP_ID% --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region %REGION%
aws ec2 authorize-security-group-ingress --group-id %SECURITY_GROUP_ID% --protocol tcp --port 8501 --cidr 0.0.0.0/0 --region %REGION%

docker build -t nsf-ai-app .
docker save nsf-ai-app:latest > nsf-ai-app.tar

(
echo #!/bin/bash
echo yum update -y
echo yum install -y docker
echo service docker start
echo usermod -a -G docker ec2-user
echo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
echo chmod +x /usr/local/bin/docker-compose
echo sleep 10
echo mkdir -p /home/ec2-user/app
echo cd /home/ec2-user/app
echo cat ^> docker-compose.yml ^<^< 'EOF'
echo version: '3.8'
echo services:
echo   api:
echo     image: nsf-ai-app:latest
echo     ports:
echo       - "8000:8000"
echo     environment:
echo       - DATABASE_URL=%DATABASE_URL%
echo       - SECRET_KEY=super-secret-key-%RANDOM%
echo       - OPENAI_API_KEY=%OPENAI_API_KEY%
echo       - S3_BUCKET_NAME=%BUCKET_NAME%
echo       - AWS_REGION=%REGION%
echo       - GRAPHRAG_WORKING_DIR=/app/nsf_graphrag_knowledge
echo     restart: unless-stopped
echo     command: uvicorn app.main:app --host 0.0.0.0 --port 8000
echo   frontend:
echo     image: nsf-ai-app:latest
echo     ports:
echo       - "80:8501"
echo       - "8501:8501"
echo     environment:
echo       - API_BASE_URL=http://localhost:8000/api
echo     restart: unless-stopped
echo     command: streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
echo     depends_on:
echo       - api
echo EOF
echo chown -R ec2-user:ec2-user /home/ec2-user/app
) > user-data.sh

aws ec2 run-instances --image-id ami-0c02fb55956c7d316 --count 1 --instance-type %INSTANCE_TYPE% --key-name %KEY_NAME% --security-group-ids %SECURITY_GROUP_ID% --user-data file://user-data.sh --region %REGION% --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=NSF-AI-App}]"

timeout /t 30 /nobreak

for /f "tokens=*" %%i in ('aws ec2 describe-instances --filters "Name=tag:Name,Values=NSF-AI-App" "Name=instance-state-name,Values=pending,running" --query "Reservations[0].Instances[0].InstanceId" --output text --region %REGION%') do set INSTANCE_ID=%%i

aws ec2 wait instance-running --instance-ids %INSTANCE_ID% --region %REGION%

for /f "tokens=*" %%i in ('aws ec2 describe-instances --instance-ids %INSTANCE_ID% --query "Reservations[0].Instances[0].PublicIpAddress" --output text --region %REGION%') do set PUBLIC_IP=%%i

timeout /t 180 /nobreak

echo Copying Docker image...
scp -i %KEY_NAME%.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL nsf-ai-app.tar ec2-user@%PUBLIC_IP%:~/

echo Starting services...
ssh -i %KEY_NAME%.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ec2-user@%PUBLIC_IP% "sudo docker load < nsf-ai-app.tar && cd app && sudo docker-compose up -d"

del user-data.sh 2>nul
del nsf-ai-app.tar 2>nul

echo.
echo App: http://%PUBLIC_IP%
echo API: http://%PUBLIC_IP%:8000
echo SSH: ssh -i %KEY_NAME%.pem ec2-user@%PUBLIC_IP%