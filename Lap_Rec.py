import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from pymongo import MongoClient
import uuid
import datetime

class TicketingSystem:
    def __init__(self):
        # Initialize an empty list to store tickets
        self.tickets = []
    
    def create_ticket(self, issue_description):
        # Generate a unique ticket ID
        ticket_id = str(uuid.uuid4())
        # Create a ticket entry
        ticket = {
            'ticket_id': ticket_id,
            'description': issue_description,
            'status': 'Open',
            'created_at': datetime.datetime.now()
        }
        # Add to ticket list
        self.tickets.append(ticket)
        return ticket_id

    def get_tickets(self):
        return self.tickets

    def update_ticket(self, ticket_id, status):
        for ticket in self.tickets:
            if ticket['ticket_id'] == ticket_id:
                ticket['status'] = status
                return True
        return False

class PredictiveMaintenance:
    def __init__(self):
        # Connect to MongoDB for maintenance data
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['maintenance_data']
    
    def predict_maintenance(self, laptop_name):
        # Query MongoDB for maintenance data
        maintenance_record = self.collection.find_one({'Laptop Name': laptop_name})
        
        if maintenance_record:
            # Extract and return the maintenance status
            return maintenance_record.get('Maintenance Status', 'No data available')
        else:
            return 'No data available'

    def update_maintenance_status(self, laptop_name, new_status):
        # Update the maintenance status in MongoDB
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
        # Connect to MongoDB for onboarding and offboarding data
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['onboarding_offboarding_data']

    def assign_laptop(self, employee_id, name, role, laptop_name):
        # Assign laptop to employee and record assignment
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
        # Mark the laptop as returned and delete the entry
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
        # Connect to MongoDB for reservations
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['available_laptops']
    
    def reserve_laptop(self, laptop_name, manager_name):
        # Reserve a laptop for a manager
        result = self.collection.update_one(
            {'Laptop Name': laptop_name, 'Reserved.reserved_by': None},
            {'$set': {'Reserved.reserved_by': manager_name, 'Reserved.reservation_date': datetime.datetime.now()}}
        )
        if result.modified_count > 0:
            return f"Laptop '{laptop_name}' reserved by '{manager_name}'."
        else:
            return f"Laptop '{laptop_name}' is not available for reservation or already reserved."

    def check_reservation(self, laptop_name):
        # Check the reservation status of a laptop
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
        # Connect to MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Laptops']
        self.collection = self.db['available_laptops']
        
        # Load your dataset with roles and recommended laptops
        self.data = pd.read_csv('train_laptops.csv')
        
        # Load dataset of available laptops from MongoDB
        self.available_laptops = pd.DataFrame(list(self.collection.find({}, {'_id': 0, 'Laptop Name': 1, 'Required GPU': 1})))
        
        # Data Cleaning
        self.data['Required CPU Speed (GHz)'] = self.data['Required CPU Speed (GHz)'].replace(',', '', regex=True).astype(float)
        self.data['Required RAM (GB)'] = self.data['Required RAM (GB)'].replace(',', '', regex=True).astype(int)
        self.data['Required Storage (GB)'] = self.data['Required Storage (GB)'].replace(',', '', regex=True).astype(int)
        
        # Convert categorical data to numerical data
        self.data['Role'] = self.data['Role'].astype('category')
        self.data['Recommended Laptop'] = self.data['Recommended Laptop'].astype('category')
        
        # Create mappings
        self.role_mapping = dict(enumerate(self.data['Role'].cat.categories))
        role_code_mapping = self.data['Role'].cat.codes
        self.reverse_role_code_mapping = dict(zip(role_code_mapping, self.data['Role']))
        
        laptop_mapping = self.data['Recommended Laptop'].cat.codes
        self.reverse_laptop_mapping = dict(zip(laptop_mapping, self.data['Recommended Laptop']))
        
        self.data['Role'] = role_code_mapping
        self.data['Recommended Laptop'] = laptop_mapping
        
        # Features and target variable
        X = self.data[['Role', 'Required CPU Speed (GHz)', 'Required RAM (GB)', 'Required Storage (GB)']]
        y = self.data['Recommended Laptop']
        
        # Create polynomial features
        self.poly = PolynomialFeatures(degree=2)
        X_poly = self.poly.fit_transform(X)
        
        # Split the data into training and test sets
        X_train, X_test, y_train, y_test = train_test_split(X_poly, y, test_size=0.2, random_state=42)
        
        # Standardize features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Initialize and train k-NN model
        self.knn = KNeighborsClassifier(n_neighbors=5)
        self.knn.fit(X_train_scaled, y_train)
        
        # Initialize systems
        self.ticketing_system = TicketingSystem()
        self.predictive_maintenance = PredictiveMaintenance()
        self.onboarding_offboarding = OnboardingOffboarding()
        self.reservation_system = ReservationSystem()

    def recommend_laptop(self, role, require_gpu=None):
        if role not in self.role_mapping.values():
            ticket_id = self.ticketing_system.create_ticket(f"Role '{role}' not found in dataset.")
            return None, f"Role not found in dataset. Ticket ID: {ticket_id}"

        # Convert role to numerical value
        role_code = [code for code, r in self.role_mapping.items() if r == role][0]

        # Get the mean parameters for the provided role
        role_data = self.data[self.data['Role'] == role_code]
        mean_cpu = role_data['Required CPU Speed (GHz)'].mean()
        mean_ram = role_data['Required RAM (GB)'].mean()
        mean_storage = role_data['Required Storage (GB)'].mean()

        # Prepare input features
        input_features = pd.DataFrame([[role_code, mean_cpu, mean_ram, mean_storage]], 
                                      columns=['Role', 'Required CPU Speed (GHz)', 'Required RAM (GB)', 'Required Storage (GB)'])
        
        # Create polynomial features for the input
        input_features_poly = self.poly.transform(input_features)
        input_features_scaled = self.scaler.transform(input_features_poly)

        # Predict the recommended laptop code
        recommended_laptop_code = self.knn.predict(input_features_scaled)[0]
        
        # Convert the predicted code back to the laptop name
        recommended_laptop = self.reverse_laptop_mapping.get(recommended_laptop_code)
        if not recommended_laptop:
            ticket_id = self.ticketing_system.create_ticket(f"Recommended laptop code '{recommended_laptop_code}' not found.")
            return None, f"Recommendation failed. Ticket ID: {ticket_id}"
        
        # Check if the recommended laptop is available
        laptop_availability = self.available_laptops[self.available_laptops['Laptop Name'] == recommended_laptop]
        if laptop_availability.empty:
            ticket_id = self.ticketing_system.create_ticket(f"Laptop '{recommended_laptop}' not available.")
            return None, f"Laptop not available. Ticket ID: {ticket_id}"

        return recommended_laptop, 'Recommendation successful.'

    def onboard_employee(self, employee_id, name, role, require_gpu=None):
        # Get laptop recommendation
        laptop, status = self.recommend_laptop(role, require_gpu)
        
        if laptop:
            # Assign laptop to the employee
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

if __name__ == "__main__":
    # Create an instance of LaptopRecommendationModel
    model = LaptopRecommendationModel()
    
    while True:
        action = input("Choose action (recommend/onboard/offboard/reserve/check/exit): ").strip().lower()
        
        if action == 'recommend':
            role = input("Enter the role of the employee: ")
            gpu_input = input("Do you require a GPU? (yes/no/leave blank for no preference): ").strip().lower()
            require_gpu = None
            if gpu_input == 'yes':
                require_gpu = True
            elif gpu_input == 'no':
                require_gpu = False
            
            laptop, status = model.recommend_laptop(role, require_gpu)
            if laptop:
                print(f"Recommended laptop: {laptop}")
                print(f"Maintenance status: {status}")
            else:
                print(f"Recommendation failed: {status}")

        elif action == 'onboard':
            employee_id = input("Enter the employee ID: ")
            name = input("Enter the employee name: ")
            role = input("Enter the role of the employee: ")
            gpu_input = input("Do you require a GPU? (yes/no/leave blank for no preference): ").strip().lower()
            require_gpu = None
            if gpu_input == 'yes':
                require_gpu = True
            elif gpu_input == 'no':
                require_gpu = False
            
            message = model.onboard_employee(employee_id, name, role, require_gpu)
            print(message)

        elif action == 'offboard':
            employee_id = input("Enter the employee ID: ")
            laptop_name = input("Enter the laptop name: ")
            message = model.offboard_employee(employee_id, laptop_name)
            print(message)

        elif action == 'reserve':
            laptop_name = input("Enter the laptop name: ")
            manager_name = input("Enter the manager's name: ")
            message = model.reserve_laptop(laptop_name, manager_name)
            print(message)

        elif action == 'check':
            laptop_name = input("Enter the laptop name: ")
            message = model.check_reservation(laptop_name)
            print(message)

        elif action == 'exit':
            print("Exiting the system.")
            break

        else:
            print("Invalid action. Please choose again.")
