snow sql -f setup_image_repo.sql
cd service
docker build --rm --platform linux/amd64 -t my_echo_service_image:tutorial .   
cd .. 
REPO_URL=$(snow spcs image-repository url NA_SECURITY_URL_APP_IMAGE_DATABASE.IMAGE_SCHEMA.IMAGE_REPO)
docker tag my_echo_service_image:tutorial $REPO_URL/my_echo_service_image:tutorial    
snow spcs image-registry login  
docker push $REPO_URL/my_echo_service_image:tutorial   
snow app teardown
snow app run  