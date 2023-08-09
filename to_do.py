from flask import Flask, request, jsonify
import psycopg2
import uuid

app = Flask(__name__)
con = psycopg2.connect(host="localhost",database="postgres",user="",password="")
cursor = con.cursor()


@app.route('/api/register', methods=['POST'])
def register():
	try:
		data = request.json
		username = data['username']
		password = data['password']
		confirm_password = data['confirm_password']

		if password != confirm_password:
			return jsonify({"message":"Password and Confirm password is not same.."})

		insert_query = '''Insert into Users (username,password) values (%s, %s);'''
		cursor.execute(insert_query,(username,password))
		con.commit()

		user_query = "select * from users where username = '{}'".format(username)
		cursor.execute(user_query)
		data_cursor = cursor.fetchall()
		#print(data_cursor)
		return jsonify({"message":"Registration successful", "userid": data_cursor[0][0]}), 201
	except Exception as e:
		print(e)
		return jsonify({"message":"Invalid data format!!"}), 400


@app.route('/api/login',methods=['PUT'])
def login():
	try:
		data = request.json
		username = data['username']
		password = data['password']
		user_query = "select * from users where username = '{}'".format(username)
		cursor.execute(user_query)
		data_cursor = cursor.fetchall()
		random_uuid = str(uuid.uuid4())
		
		if username == data_cursor[0][1]:
			print("User exists..")
			if password == data_cursor[0][2]:
				user_id = data_cursor[0][0]
				auth_query = "select * from auth_key where user_id = '{}'".format(user_id)
				cursor.execute(auth_query)
				auth = cursor.fetchall()
				if len(auth)>0:
					access_token = auth[0][2]
					return jsonify({"message":"Login successful", "user_id":data_cursor[0][0], "access_token": access_token})
				else:
					insert_query = '''Insert into auth_key (user_id, access_token) values (%s, %s);'''
					cursor.execute(insert_query,(user_id,random_uuid))
					con.commit()
					return jsonify({"message":"Login successful", "user_id":data_cursor[0][0], "access_token": random_uuid})

			else:
				return jsonify({"message":"Incorrect password entered!!"})

		
	except Exception as e:
		print(e)
		return jsonify({"message":"Invalid data format!!"}), 400


@app.route('/api/tasks',methods=['POST'])
def tasks():
	try:
		data = request.json
		title = data['title']
		description = data['description']		
		
		access_token = request.headers.get("Authorization")
		
		auth_query = """select * from auth_key where access_token = '{}'""".format(access_token)
		cursor.execute(auth_query)
		auth_cursor = cursor.fetchall()


		if len(auth_cursor)>0:
			user_id = auth_cursor[0][1]
			insert_query = """Insert into tasks(user_id,title,description) values (%s, %s, %s) RETURNING ID;"""
			cursor.execute(insert_query,(user_id,title,description))
			inserted_id = cursor.fetchone()[0]
			con.commit()			
			
			return jsonify({"message":"Task created successfully", "id":inserted_id}),200

		else:
			return jsonify({"message":"Authorization Error"}), 401

	except Exception as e:
		print(e)
		return jsonify({"message":"Invalid data!!"}), 400


@app.route('/api/tasks',methods=['GET'])
def all_tasks():
	try:
		access_token = request.headers.get("Authorization")
		content = request.headers.get("Content-Type")

		auth_query = """select * from auth_key where access_token = '{}'""".format(access_token)
		cursor.execute(auth_query)
		auth_cursor = cursor.fetchall()
		user_id1 = auth_cursor[0][1]

		task_query = """select * from tasks where user_id = '{}'""".format(user_id1)
		cursor.execute(task_query)
		task_cursor = cursor.fetchall()

		list = []
		for task in task_cursor:
			d = {
				"id":task[0],
				"title":task[2],
				"description":task[3],
				"completed": not task[4]
				}
			list.append(d)
		return jsonify({"tasks":list}), 200

	except Exception as e:
		print(e)
		return jsonify({"message":"Invalid data!!"}), 400


@app.route('/api/tasks/<int:task_id>',methods=['GET'])
def get_task(task_id):
	try:
		access_token = request.headers.get('Authorization')
		content = request.headers.get('Content-Type')
		task_query = """select * from tasks where id = '{}'""".format(task_id)
		cursor.execute(task_query)
		task_cursor = cursor.fetchall()
		return jsonify({"id":task_cursor[0][0],"title":task_cursor[0][2],'description':task_cursor[0][3],'completed':not task_cursor[0][4]}), 200

	except Exception as e:
		print(e)
		return jsonify({"message":"Invalid data"}), 400


@app.route('/api/tasks/<int:task_id>',methods=['PUT'])
def update_task(task_id):
	try:
		access_token = request.headers.get("Authorization")
		content = request.headers.get('Content-Type')
		data = request.json 
		title = data['title']
		description = data['description']

		task_query = """select * from tasks where id = '{}'""".format(task_id)
		cursor.execute(task_query)
		task_cursor = cursor.fetchall()

		update_query = """update tasks set title = %s, description = %s where id = %s"""
		cursor.execute(update_query,(title,description,task_id))
		con.commit()

		return jsonify({"message":"Task updated successfully"})


	except Exception as e:
		print(e)
		return jsonify({"message":"Invalid data"}), 400


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
	try:
		access_token = request.headers.get("Authorization")
		content = request.headers.get("Content-Type")

		task_query = """select * from tasks where id = '{}'""".format(task_id)
		cursor.execute(task_query)
		task_cursor = cursor.fetchall()

		delete_query = """delete from tasks where id = '{}'""".format(task_id)
		cursor.execute(delete_query)
		con.commit()

		return jsonify({"message":"Task deleted successfully"})


	except Exception as e:
		print(e)
		return jsonify({"message":"Invalid data"}), 400



if __name__ == "__main__":
	app.run(port=8080,debug=True)