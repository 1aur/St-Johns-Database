from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import mysql.connector
from dotenv import load_dotenv
import os
import logging

load_dotenv()

app = Flask(__name__)


db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE'),
    'port': int(os.getenv('DB_PORT')),
    'ssl_disabled': True
}


@app.before_request
def before_request():
    try:
        if not hasattr(g, 'db'):
            g.db = mysql.connector.connect(**db_config)
            g.cursor = g.db.cursor()
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        raise

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'cursor'):
        g.cursor.close()
    if hasattr(g, 'db'):
        g.db.close()

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    try:
        g.cursor.execute(query, params)
        if fetch_one:
            return g.cursor.fetchone()
        if fetch_all:
            return g.cursor.fetchall()
        g.db.commit()
    except mysql.connector.Error as e:
        g.db.rollback()
        logging.error(f"MySQL Error: {e}")
        raise e 
    
def validate_inputs(inputs, rules):
    errors = []
    for field, rule in rules.items():
        value = inputs.get(field)
        if rule.get('required') and not value:
            errors.append(f"{field} is required.")
        if rule.get('type') == 'int':
            try:
                int(value)
                if rule.get('min') and int(value) < rule['min']:
                    errors.append(f"{field} must be at least {rule['min']}.")
            except ValueError:
                errors.append(f"{field} must be a valid integer.")
    return errors

    
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/students')
def students():
    return render_template('students.html')

@app.route('/instructors')
def instructors():
    return render_template('instructors.html')

@app.route('/sections')
def sections():
    return render_template('sections.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/enrollments')
def enrollments():
    return render_template('enrollments.html')

@app.route('/test')
def test_db():
    try:
        query = "SHOW TABLES"  
        g.cursor.execute(query)
        tables = g.cursor.fetchall()
        return f"Connected to the database! Tables: {tables}"
    except Exception as e:
        return f"Error: {e}"


@app.route('/search_students', methods=['GET'])
def search_students():
    search_query = request.args.get('query', '').lower()  
    print(f"Search query received: {search_query}")  # Debug log
    if not search_query:  
        return jsonify({'students': []})

    query = """
        SELECT stormcard_id, first_name, last_name
        FROM student
        WHERE LOWER(first_name) LIKE %s
    """
    try:
        search_pattern = f"{search_query}%"
        g.cursor.execute(query, (search_pattern,))  
        results = g.cursor.fetchall()
        print(f"Search results: {results}")  # Debug log

        students = [
            {'stormcard_id': row[0], 'first_name': row[1], 'last_name': row[2]}
            for row in results
        ]
        print(f"Formatted results: {students}")  # Debug log
        return jsonify({'students': students})
    except Exception as e:
        print(f"Error in search_students: {e}")  # Debug log
        return jsonify({'students': [], 'error': str(e)})

# Fetch detailed student data
@app.route('/get_student_data', methods=['GET'])
def get_student_data():
    stormcard_id = request.args.get('stormcard_id', '')  
    print(f"Fetching student data for ID: {stormcard_id}")  # Debug log
    query = """
        SELECT stormcard_id, first_name, last_name, date_of_birth, email, major, gpa, phone_number, address
        FROM student
        WHERE stormcard_id = %s
    """
    g.cursor.execute(query, (stormcard_id,))
    result = g.cursor.fetchone()
    print(f"Student data result: {result}")  # Debug log

    if result:
        # Convert date object to string format
        date_of_birth = result[3].strftime('%Y-%m-%d') if result[3] else None
        
        response = {
            'stormcard_id': result[0],
            'first_name': result[1],
            'last_name': result[2],
            'date_of_birth': date_of_birth,
            'email': result[4],
            'major': result[5],
            'gpa': str(result[6]) if result[6] else None,  # Convert float to string
            'phone_number': result[7],
            'address': result[8]
        }
        print(f"Formatted response: {response}")  # Debug log
        return jsonify(response)
    else:
        return jsonify({'error': 'Student not found'}), 404


#Insert New Student
@app.route('/insert_student', methods=['GET', 'POST'])
def insert_student():
    if request.method == 'POST':
        # Get data from the form
        stormcard_id = request.form.get('stormcard_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        email = request.form.get('email')
        major = request.form.get('major')
        gpa = request.form.get('gpa')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')

        # Insert the student into the database
        query = """
            INSERT INTO student (stormcard_id, first_name, last_name, date_of_birth, email, major, gpa, phone_number, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            g.cursor.execute(query, (stormcard_id, first_name, last_name, date_of_birth, email, major, gpa, phone_number, address))
            g.db.commit()
            return redirect('/students')  
        except Exception as e:
            return f"An error occurred: {e}"

 
    return render_template('insert_student.html')


# Update Student information
@app.route('/update_student', methods=['GET', 'POST'])
def update_student():
    if request.method == 'POST':
        # Get updated data from the form
        stormcard_id = request.form.get('stormcard_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        email = request.form.get('email')
        major = request.form.get('major')
        gpa = request.form.get('gpa')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')

        # Update the student in the database
        query = """
            UPDATE student
            SET first_name = %s, last_name = %s, date_of_birth = %s, email = %s,
                major = %s, gpa = %s, phone_number = %s, address = %s
            WHERE stormcard_id = %s
        """
        try:
            g.cursor.execute(query, (first_name, last_name, date_of_birth, email, major, gpa, phone_number, address, stormcard_id))
            g.db.commit()
            return redirect('/students')  
        except Exception as e:
            return f"An error occurred: {e}"

    # Fetch the student details to pre-fill the form
    stormcard_id = request.args.get('stormcard_id') 
    query = "SELECT * FROM student WHERE stormcard_id = %s"
    g.cursor.execute(query, (stormcard_id,))
    student = g.cursor.fetchone()

    if student:
        return render_template('update_student.html', student=student)
    else:
        return "Student not found", 404


# delete student
@app.route('/delete_student', methods=['POST'])
def delete_student():
    stormcard_id = request.form.get('stormcard_id')

    if not stormcard_id:
        return "Error: No Stormcard ID provided", 400

    query = "DELETE FROM student WHERE stormcard_id = %s"
    try:
        g.cursor.execute(query, (stormcard_id,))
        g.db.commit()
        if g.cursor.rowcount > 0:
            return redirect('/students') 
        else:
            return "Error: Student not found", 404
    except Exception as e:
        return f"An error occurred: {e}"



# Search Instructors
@app.route('/search_instructors', methods=['GET'])
def search_instructors():
    search_query = request.args.get('query', '').lower()  
    print(f"Search query received: {search_query}")  # Debug log
    if not search_query:  
        return jsonify({'instructors': []})

    query = """
        SELECT instructor_id, first_name, last_name
        FROM instructors
        WHERE LOWER(first_name) LIKE %s
    """
    try:
        g.cursor.execute(query, (f"{search_query}%",))  
        results = g.cursor.fetchall()
        print(f"Query results: {results}")  # Debug log
        
        instructors = [
            {'instructor_id': row[0], 'first_name': row[1], 'last_name': row[2]}
            for row in results
        ]
        print(f"Formatted results: {instructors}")  # Debug log
        return jsonify({'instructors': instructors})
    except Exception as e:
        print(f"Error in search_instructors: {e}")  # Debug log
        return jsonify({'instructors': [], 'error': str(e)})

# Fetch instructor data
@app.route('/get_instructor_data', methods=['GET'])
def get_instructor_data():
    instructor_id = request.args.get('instructor_id', '') 
    print(f"Fetching instructor with ID: {instructor_id}")  # Debug log
    
    query = """
        SELECT instructor_id, first_name, last_name, date_of_birth, email, hire_date, tenure, salary, course_id
        FROM instructors
        WHERE instructor_id = %s
    """
    try:
        g.cursor.execute(query, (instructor_id,))
        result = g.cursor.fetchone()
        print(f"Query result: {result}")  # Debug log

        if result:
            # Convert date objects to string format
            date_of_birth = result[3].strftime('%Y-%m-%d') if result[3] else None
            hire_date = result[5].strftime('%Y-%m-%d') if result[5] else None
            
            response = {
                'instructor_id': result[0],
                'first_name': result[1],
                'last_name': result[2],
                'date_of_birth': date_of_birth,
                'email': result[4],
                'hire_date': hire_date,
                'tenure': result[6],
                'salary': str(result[7]) if result[7] else None,  # Convert Decimal to string
                'course_id': result[8]
            }
            print(f"Formatted response: {response}")  # Debug log
            return jsonify(response)
        else:
            return jsonify({'error': 'Instructor not found'}), 404
    except Exception as e:
        print(f"Error in get_instructor_data: {e}")  # Debug log
        return jsonify({'error': str(e)}), 500


# Insert New Instructor
@app.route('/insert_instructor', methods=['GET', 'POST'])
def insert_instructor():
    if request.method == 'POST':
        instructor_id = request.form.get('instructor_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        email = request.form.get('email')
        hire_date = request.form.get('hire_date')
        tenure = request.form.get('tenure')
        salary = request.form.get('salary')
        course_id = request.form.get('course_id')

        query = """
            INSERT INTO instructors (instructor_id, first_name, last_name, date_of_birth, email, hire_date, tenure, salary, course_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            g.cursor.execute(query, (instructor_id, first_name, last_name, date_of_birth, email, hire_date, tenure, salary, course_id))
            g.db.commit()
            return redirect('/instructors')
        except Exception as e:
            g.db.rollback() 
            return f"An error occurred: {e}"

    return render_template('insert_instructor.html')

# Update Instructor information
@app.route('/update_instructor', methods=['GET', 'POST'])
def update_instructor():
    if request.method == 'POST':
        instructor_id = request.form.get('instructor_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        email = request.form.get('email')
        hire_date = request.form.get('hire_date')
        tenure = request.form.get('tenure')
        salary = request.form.get('salary')
        course_id = request.form.get('course_id')

        query = """
            UPDATE instructors
            SET first_name = %s, last_name = %s, date_of_birth = %s, email = %s,
                hire_date = %s, tenure = %s, salary = %s, course_id = %s
            WHERE instructor_id = %s
        """
        try:
            g.cursor.execute(query, (first_name, last_name, date_of_birth, email, hire_date, tenure, salary, course_id, instructor_id))
            g.db.commit()
            return redirect('/instructors') 
        except Exception as e:
            return f"An error occurred: {e}"

    instructor_id = request.args.get('instructor_id')
    query = "SELECT * FROM instructors WHERE instructor_id = %s"
    g.cursor.execute(query, (instructor_id,))
    instructor = g.cursor.fetchone()

    if instructor:
        return render_template('update_instructor.html', instructor=instructor)
    else:
        return "Instructor not found", 404

# Delete Instructor
@app.route('/delete_instructor', methods=['POST'])
def delete_instructor():
    instructor_id = request.form.get('instructor_id')

    if not instructor_id:
        return "Error: No Instructor ID provided", 400

    query = "DELETE FROM instructors WHERE instructor_id = %s"
    try:
        g.cursor.execute(query, (instructor_id,))
        g.db.commit()
        if g.cursor.rowcount > 0:
            return redirect('/instructors')
        else:
            return "Error: Instructor not found", 404
    except Exception as e:
        return f"An error occurred: {e}"

# Search Courses
@app.route('/search_courses', methods=['GET'])
def search_courses():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify({'courses': []})

    sql = "SELECT course_id, course_name, department FROM course WHERE LOWER(course_name) LIKE %s"
    results = execute_query(sql, (f"{query}%",), fetch_all=True)

    if not results:
        return jsonify({'error': 'No courses found'}), 404

    return jsonify({'courses': [{'id': row[0], 'course_name': row[1], 'department': row[2]} for row in results]})


@app.route('/get_course_data', methods=['GET'])
def get_course_data():
    course_id = request.args.get('id', '')
    sql = """
        SELECT course_id, course_name, credit, subject, campus, course_description, prerequisites, max_capacity, department, college
        FROM course
        WHERE course_id = %s
    """
    result = execute_query(sql, (course_id,), fetch_one=True)

    if result:
        return jsonify({
            'id': result[0],
            'name': result[1],
            'credit': result[2],
            'subject': result[3],
            'campus': result[4],
            'description': result[5],
            'prerequisites': result[6],
            'max_capacity': result[7],
            'department': result[8],
            'college': result[9],
        })
    else:
        return jsonify({'error': 'Course not found'}), 404

# Insert New Course
@app.route('/insert_course', methods=['GET', 'POST'])
def insert_course():
    if request.method == 'POST':
        rules = {
            'course_id': {'required': True},
            'course_name': {'required': True},
            'credit': {'required': True, 'type': 'int', 'min': 1},
            'max_capacity': {'required': True, 'type': 'int', 'min': 1},
        }
        errors = validate_inputs(request.form, rules)
        if errors:
            return render_template('insert_course.html', errors=errors, form_data=request.form)

        query = """
            INSERT INTO course (course_id, course_name, credit, subject, campus, college, course_description, prerequisites, max_capacity, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            request.form['course_id'],
            request.form['course_name'],
            request.form['credit'],
            request.form['subject'],
            request.form['campus'],
            request.form['college'],
            request.form['course_description'],
            request.form['prerequisites'],
            request.form['max_capacity'],
            request.form['department'],
        )
        try:
            execute_query(query, params)
            return redirect(url_for('courses'))
        except Exception as e:
            return render_template('insert_course.html', errors=[f"Database error: {e}"], form_data=request.form)

    return render_template('insert_course.html', errors=None, form_data={})



# Update Course Information
@app.route('/update_course', methods=['GET', 'POST'])
def update_course():
    if request.method == 'POST':
        course_id = request.form.get('id')
        course_name = request.form.get('course_name')
        course_description = request.form.get('course_description')
        credit = request.form.get('credit')
        department = request.form.get('department')
        prerequisites = request.form.get('prerequisites')
        max_capacity = request.form.get('max_capacity')
        subject = request.form.get('subject')
        campus = request.form.get('campus')

        query = """
            UPDATE course
            SET course_name = %s, course_description = %s, credit = %s, subject = %s, campus = %s, 
                prerequisites = %s, max_capacity = %s, department = %s
            WHERE course_id = %s
        """
        try:
            execute_query(query, (course_name, course_description, credit, subject, campus, prerequisites, max_capacity, department, course_id))
            return redirect(url_for('courses'))
        except Exception as e:
            return f"An error occurred: {e}"

    course_id = request.args.get('id')
    query = """
        SELECT course_id, course_name, credit, subject, campus, college, course_description, prerequisites, max_capacity, department
        FROM course
        WHERE course_id = %s
    """
    course = execute_query(query, (course_id,), fetch_one=True)

    if course:
        return render_template('update_course.html', course=course)
    else:
        return "Course not found", 404


# Delete Course
@app.route('/delete_course', methods=['POST'])
def delete_course():
    course_id = request.form.get('id')

    if not course_id:
        return "Error: No Course ID provided", 400

    query = "DELETE FROM course WHERE course_id = %s"
    try:
        execute_query(query, (course_id,))
        return redirect(url_for('courses'))
    except Exception as e:
        return f"An error occurred: {e}"

# Search Sections
@app.route('/search_sections', methods=['GET'])
def search_sections():
    search_query = request.args.get('query', '').lower()  
    if not search_query: 
        return jsonify({'sections': []})

    query = """
        SELECT section_id, year, room_location, instructor_id, course_id, semester
        FROM section
        WHERE LOWER(section_id) LIKE %s OR LOWER(year) LIKE %s OR LOWER(room_location) LIKE %s
    """
    try:
        search_like = f"%{search_query}%"
        g.cursor.execute(query, (search_like, search_like, search_like))  
        results = g.cursor.fetchall()

        sections = [
            {'section_id': row[0], 'year': row[1], 'room_location': row[2], 'instructor_id': row[3], 'course_id': row[4], 'semester': row[5]}
            for row in results
        ]
        return jsonify({'sections': sections})
    except Exception as e:
        print(f"Error in search_sections: {e}")  # Debug log
        return jsonify({'sections': [], 'error': str(e)})

# Get Section Data
@app.route('/get_section_data', methods=['GET'])
def get_section_data():
    section_id = request.args.get('section_id', '')
    query = """
        SELECT section_id, year, room_location, instructor_id, course_id, semester
        FROM section
        WHERE section_id = %s
    """
    g.cursor.execute(query, (section_id,))
    result = g.cursor.fetchone()

    if result:
        return jsonify({
            'section_id': result[0],
            'year': result[1],
            'room_location': result[2],
            'instructor_id': result[3],
            'course_id': result[4],
            'semester': result[5]
        })
    else:
        return jsonify({'error': 'Section not found'}), 404
    
#Update Section
@app.route('/update_section', methods=['GET', 'POST'])
def update_section():
    if request.method == 'POST':
        section_id = request.form.get('section_id')
        year = request.form.get('year')
        room_location = request.form.get('room_location')
        instructor_id = request.form.get('instructor_id')
        course_id = request.form.get('course_id')
        semester = request.form.get('semester')

        query = """
            UPDATE section
            SET year = %s, room_location = %s, instructor_id = %s, course_id = %s, semester = %s
            WHERE section_id = %s
        """
        try:
            g.cursor.execute(query, (year, room_location, instructor_id, course_id, semester, section_id))
            g.db.commit()
            return redirect('/sections') 
        except Exception as e:
            return f"An error occurred: {e}"

    section_id = request.args.get('section_id')  
    query = "SELECT * FROM section WHERE section_id = %s"
    g.cursor.execute(query, (section_id,))
    section = g.cursor.fetchone()

    if section:
        return render_template('update_section.html', section=section)
    else:
        return "Section not found", 404

# Insert Section
@app.route('/insert_section', methods=['GET', 'POST'])
def insert_section():
    if request.method == 'POST':
        section_id = request.form.get('section_id')
        year = request.form.get('year')
        room_location = request.form.get('room_location')
        instructor_id = request.form.get('instructor_id')
        course_id = request.form.get('course_id')
        semester = request.form.get('semester')

        query = """
            INSERT INTO section (section_id, year, room_location, instructor_id, course_id, semester)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            g.cursor.execute(query, (section_id, year, room_location, instructor_id, course_id, semester))
            g.db.commit()
            return redirect('/sections')  
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('insert_section.html')

# Delete Section
@app.route('/delete_section', methods=['POST'])
def delete_section():
    section_id = request.form.get('section_id')

    if not section_id:
        return "Error: No Section ID provided", 400

    query = "DELETE FROM section WHERE section_id = %s"
    try:
        execute_query(query, (section_id,))
        return redirect('/sections')  
    except Exception as e:
        return f"An error occurred: {e}"


# Search Enrollments
@app.route('/search_enrollments', methods=['GET'])
def search_enrollments():
    search_query = request.args.get('query', '').lower()  
    if not search_query:  
        return jsonify({'enrollments': []})

    query = """
        SELECT section_id, enrollment_date, grade, enrollment_status, stormcard_id
        FROM enrollments
        WHERE LOWER(stormcard_id) LIKE %s
    """
    try:
        g.cursor.execute(query, (f"{search_query}%",))  
        results = g.cursor.fetchall()

        enrollments = [
            {'section_id': row[0], 'enrollment_date': row[1], 'grade': row[2], 'enrollment_status': row[3], 'stormcard_id': row[4]}
            for row in results
        ]
        return jsonify({'enrollments': enrollments})
    except Exception as e:
        print(f"Error in search_enrollments: {e}")  # Debug log
        return jsonify({'enrollments': [], 'error': str(e)})

@app.route('/get_enrollment_data', methods=['GET'])
def get_enrollment_data():
    stormcard_id = request.args.get('stormcard_id', '')  
    query = """
        SELECT section_id, enrollment_date, grade, enrollment_status, stormcard_id
        FROM enrollments
        WHERE stormcard_id = %s
    """
    g.cursor.execute(query, (stormcard_id,))
    result = g.cursor.fetchone()

    if result:
        return {
            'section_id': result[0],
            'enrollment_date': result[1],
            'grade': result[2],
            'enrollment_status': result[3],
            'stormcard_id': result[4]
        }
    else:
        return {'error': 'Enrollment not found'}, 404

# Insert New Enrollment
@app.route('/insert_enrollment', methods=['GET', 'POST'])
def insert_enrollment():
    if request.method == 'POST':
        section_id = request.form.get('section_id')
        enrollment_date = request.form.get('enrollment_date')
        grade = request.form.get('grade')
        enrollment_status = request.form.get('enrollment_status')
        stormcard_id = request.form.get('stormcard_id')

        query = """
            INSERT INTO enrollments (section_id, enrollment_date, grade, enrollment_status, stormcard_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            g.cursor.execute(query, (section_id, enrollment_date, grade, enrollment_status, stormcard_id))
            g.db.commit()
            return redirect('/enrollments')  
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template('insert_enrollments.html')

# Update Enrollment information
@app.route('/update_enrollment', methods=['GET', 'POST'])
def update_enrollment():
    stormcard_id = request.args.get('stormcard_id')  

    if not stormcard_id:
        return "Stormcard ID is missing", 400  

    query = "SELECT * FROM enrollments WHERE stormcard_id = %s"
    g.cursor.execute(query, (stormcard_id,))
    enrollment = g.cursor.fetchone()

    if enrollment:
        return render_template('update_enrollments.html', enrollment=enrollment)
    else:
        return f"Enrollment with Stormcard ID {stormcard_id} not found", 404  



# Delete Enrollment
@app.route('/delete_enrollment', methods=['POST'])
def delete_enrollment():
    stormcard_id = request.form.get('stormcard_id')

    if not stormcard_id:
        return "Error: No Stormcard ID provided", 400

    query = "DELETE FROM enrollments WHERE stormcard_id = %s"
    try:
        g.cursor.execute(query, (stormcard_id,))
        g.db.commit()
        if g.cursor.rowcount > 0:
            return redirect('/enrollments')  
        else:
            return "Error: Enrollment not found", 404
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)