import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        user="murali",
        password="murali123",
        database="productivity_agent"
    )

    print("SUCCESSFULLY CONNECTED!")

except Exception as e:
    print("ERROR:")
    print(e)