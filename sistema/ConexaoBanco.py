import redis
conR = redis.Redis(host='redis-17733.c11.us-east-1-2.ec2.redns.redis-cloud.com:17733',
    port=10339,
    password='FX4HKWXiS1lTASjrm1SE7nWKhqJtW55s'
)

conR.set('user.name','Silmara')

print(conR.set('user.name'))