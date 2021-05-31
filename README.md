##Install dependencies
````
python3 -m vevn venv
source venv/bin/activate
pip3 install -r requirements.txt
````
##Run container
```
docker-compose build
docker-compose up -d
```
##Init db
```
docker-compose exec backend /bin/bash
alembic upgrade head
exit
```

##Tests
```
python3 -m pytest tests/test_backend.py
```

###Docs
http://127.0.0.1:8000/docs

http://127.0.0.1:8000/redoc
