from flask import Flask, request, jsonify
from pymongo import MongoClient
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
import uuid
import datetime

app = Flask(__name__)

class TicketingSystem:
    def __init__(self):
        self.tickets = []

    def create_ticket(self, issue_description):
        ticket_id = str(uuid.uuid4())
        ticket = {
            'ticket_id': ticket_id,
            'description': issue_description,
            'status': 'Open',
            'created_at': datetime.datetime.now()
        }
        self.tickets.append(ticket)
        return ticket_id

class PredictiveMaintenance:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['maintenance_data']

    def predict_maintenance(self, laptop_name):
        maintenance_record = self.collection.find_one({'Laptop Name': laptop_name})
        if maintenance_record:
            return maintenance_record.get('Maintenance Status', 'No data available')
        else:
            return 'No data available'

    def update_maintenance_status(self, laptop_name, new_status):
        result = self.collection.update_one(
            {'Laptop Name': laptop_name},
            {'$set': {'Maintenance Status': new_status, 'last_updated': datetime.datetime.now()}}
        )
        if result.modified_count > 0:
            return 'Maintenance status updated successfully.'
        else:
            return 'Failed to update maintenance status.'

class OnboardingOffboarding:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['onboarding_offboarding_data']

    def assign_laptop(self, employee_id, name, role, laptop_name):
        assignment = {
            'employee_id': employee_id,
            'name': name,
            'role': role,
            'laptop_assigned': laptop_name,
            'status': 'Onboarding',
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        self.collection.insert_one(assignment)
        return f"Laptop '{laptop_name}' assigned to employee '{employee_id}'."

    def return_laptop(self, employee_id, laptop_name):
        result = self.collection.update_one(
            {'employee_id': employee_id, 'laptop_assigned': laptop_name, 'status': 'Onboarding'},
            {'$set': {'status': 'Offboarding', 'return_date': datetime.datetime.now().strftime('%Y-%m-%d')}}
        )
        if result.matched_count > 0:
            self.collection.delete_one({'employee_id': employee_id, 'laptop_assigned': laptop_name, 'status': 'Offboarding'})
            return f"Laptop '{laptop_name}' returned by employee '{employee_id}' and record deleted."
        else:
            return f"No active assignment found for laptop '{laptop_name}' with employee '{employee_id}'."

class ReservationSystem:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['available_laptops']
    
    def reserve_laptop(self, laptop_name, manager_name):
        result = self.collection.update_one(
            {'Laptop Name': laptop_name, 'Reserved.reserved_by': None},
            {'$set': {'Reserved.reserved_by': manager_name, 'Reserved.reservation_date': datetime.datetime.now()}}
        )
        if result.modified_count > 0:
            return f"Laptop '{laptop_name}' reserved by '{manager_name}'."
        else:
            return f"Laptop '{laptop_name}' is not available for reservation or already reserved."

    def check_reservation(self, laptop_name):
        laptop = self.collection.find_one({'Laptop Name': laptop_name})
        if laptop:
            reserved_by = laptop['Reserved']['reserved_by']
            if reserved_by:
                return f"Laptop '{laptop_name}' is reserved by '{reserved_by}'."
            else:
                return f"Laptop '{laptop_name}' is not reserved."
        else:
            return f"Laptop '{laptop_name}' not found."

class LaptopRecommendationModel:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['available_laptops']
        
        self.data = pd.read_csv('train_laptops.csv')
        self.available_laptops = pd.DataFrame(list(self.collection.find({}, {'_id': 0, 'Laptop Name': 1, 'Required GPU': 1})))
        
        self.data['Required CPU Speed (GHz)'] = self.data['Required CPU Speed (GHz)'].replace(',', '', regex=True).astype(float)
        self.data['Required RAM (GB)'] = self.data['Required RAM (GB)'].replace(',', '', regex=True).astype(int)
        self.data['Required Storage (GB)'] = self.data['Required Storage (GB)'].replace(',', '', regex=True).astype(int)
        
        self.data['Role'] = self.data['Role'].astype('category')
        self.data['Recommended Laptop'] = self.data['Recommended Laptop'].astype('category')
        
        self.role_mapping = dict(enumerate(self.data['Role'].cat.categories))
        role_code_mapping = self.data['Role'].cat.codes
        self.reverse_role_code_mapping = dict(zip(role_code_mapping, self.data['Role']))
        
        laptop_mapping = self.data['Recommended Laptop'].cat.codes
        self.reverse_laptop_mapping = dict(zip(laptop_mapping, self.data['Recommended Laptop']))
        
        self.data['Role'] = role_code_mapping
        self.data['Recommended Laptop'] = laptop_mapping
        
        X = self.data[['Role', 'Required CPU Speed (GHz)', 'Required RAM (GB)', 'Required Storage (GB)']]
        y = self.data['Recommended Laptop']
        
        self.poly = PolynomialFeatures(degree=2)
        X_poly = self.poly.fit_transform(X)
        
        X_train, X_test, y_train, y_test = train_test_split(X_poly, y, test_size=0.2, random_state=42)
        
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.knn = KNeighborsClassifier(n_neighbors=5)
        self.knn.fit(X_train_scaled, y_train)
        
        self.ticketing_system = TicketingSystem()
        self.predictive_maintenance = PredictiveMaintenance()
        self.onboarding_offboarding = OnboardingOffboarding()
        self.reservation_system = ReservationSystem()

    def recommend_laptop(self, role, require_gpu=None):
        if role not in self.role_mapping.values():
            ticket_id = self.ticketing_system.create_ticket(f"Role '{role}' not found in dataset.")
            return None, f"Role not found in dataset. Ticket ID: {ticket_id}"

        role_code = [code for code, r in self.role_mapping.items() if r == role][0]
        role_data = self.data[self.data['Role'] == role_code]
        mean_cpu = role_data['Required CPU Speed (GHz)'].mean()
        mean_ram = role_data['Required RAM (GB)'].mean()
        mean_storage = role_data['Required Storage (GB)'].mean()

        input_features = pd.DataFrame([[role_code, mean_cpu, mean_ram, mean_storage]], 
                                      columns=['Role', 'Required CPU Speed (GHz)', 'Required RAM (GB)', 'Required Storage (GB)'])
        
        input_features_poly = self.poly.transform(input_features)
        input_features_scaled = self.scaler.transform(input_features_poly)

        recommended_laptop_code = self.knn.predict(input_features_scaled)[0]
        
        recommended_laptop = self.reverse_laptop_mapping.get(recommended_laptop_code)
        if not recommended_laptop:
            ticket_id = self.ticketing_system.create_ticket(f"Recommended laptop code '{recommended_laptop_code}' not found.")
            return None, f"Recommendation failed. Ticket ID: {ticket_id}"
        
        laptop_availability = self.available_laptops[self.available_laptops['Laptop Name'] == recommended_laptop]
        if laptop_availability.empty:
            ticket_id = self.ticketing_system.create_ticket(f"Laptop '{recommended_laptop}' not available.")
            return None, f"Laptop not available. Ticket ID: {ticket_id}"

        return recommended_laptop, 'Recommendation successful.'

    def onboard_employee(self, employee_id, name, role, require_gpu=None):
        laptop, status = self.recommend_laptop(role, require_gpu)
        if laptop:
            assignment_message = self.onboarding_offboarding.assign_laptop(employee_id, name, role, laptop)
            return f"{assignment_message} Maintenance status: {status}"
        else:
            return status

    def offboard_employee(self, employee_id, laptop_name):
        return self.onboarding_offboarding.return_laptop(employee_id, laptop_name)

    def reserve_laptop(self, laptop_name, manager_name):
        return self.reservation_system.reserve_laptop(laptop_name, manager_name)

    def check_reservation(self, laptop_name):
        return self.reservation_system.check_reservation(laptop_name)

model = LaptopRecommendationModel()

@app.route('/recommend', methods=['POST'])
def recommend_laptop():
    data = request.json
    role = data.get('role')
    require_gpu = data.get('require_gpu', None)
    laptop, status = model.recommend_laptop(role, require_gpu)
    if laptop:
        return jsonify({'laptop': laptop, 'status': status}), 200
    else:
        return jsonify({'error': status}), 400

@app.route('/onboard', methods=['POST'])
def onboard_employee():
    data = request.json
    employee_id = data.get('employee_id')
    name = data.get('name')
    role = data.get('role')
    require_gpu = data.get('require_gpu', None)
    message = model.onboard_employee(employee_id, name, role, require_gpu)
    return jsonify({'message': message}), 200

@app.route('/offboard', methods=['POST'])
def offboard_employee():
    data = request.json
    employee_id = data.get('employee_id')
    laptop_name = data.get('laptop_name')
    message = model.offboard_employee(employee_id, laptop_name)
    return jsonify({'message': message}), 200

@app.route('/reserve', methods=['POST'])
def reserve_laptop():
    data = request.json
    laptop_name = data.get('laptop_name')
    manager_name = data.get('manager_name')
    message = model.reserve_laptop(laptop_name, manager_name)
    return jsonify({'message': message}), 200

@app.route('/check', methods=['POST'])
def check_reservation():
    data = request.get_json()  # Get the JSON data from the request
    laptop_name = data.get('laptop_name')  # Extract the laptop_name from the JSON data
    
    if not laptop_name:
        return jsonify({"message": "Laptop name is required."}), 400

    result = model.check_reservation(laptop_name)  # Call the check_reservation method
    return jsonify({"message": result})


if __name__ == '__main__':
    app.run(debug=True)
