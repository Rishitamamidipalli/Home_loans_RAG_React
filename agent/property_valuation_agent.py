import boto3
import json
import os
import pickle
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score

class PropertyValuationAgent:
    """
    Property Valuation Agent for the home loan workflow
    Uses ML models and rule-based valuation to estimate property values
    """
    
    def __init__(self, bucket_name="sarma-1", region_name="us-east-1"):
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", region_name=region_name)
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.is_model_trained = False
        self.models_dir = "saved_models"
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        self.startup_model_loaded = False
        
        # Try to load existing models
        self._load_existing_models()

    def _load_existing_models(self):
        """Load existing ML models if available"""
        try:
            # Check for existing model files in root directory
            model_files = [
                "property_valuation_model.pkl",
                "property_valuation_model_scaler.pkl", 
                "property_valuation_model_encoders.pkl",
                "property_valuation_model_metadata.pkl"
            ]
            
            all_exist = all(os.path.exists(f) for f in model_files)
            if all_exist:
                print("✅ Found all ML model files in root directory")
                # Load models directly from root directory
                with open("property_valuation_model.pkl", 'rb') as f:
                    self.model = pickle.load(f)
                with open("property_valuation_model_scaler.pkl", 'rb') as f:
                    self.scaler = pickle.load(f)
                with open("property_valuation_model_encoders.pkl", 'rb') as f:
                    self.label_encoders = pickle.load(f)
                with open("property_valuation_model_metadata.pkl", 'rb') as f:
                    metadata = pickle.load(f)
                    self.is_model_trained = metadata.get('is_model_trained', True)
                    if 'training_accuracy' in metadata:
                        self.training_accuracy = metadata['training_accuracy']
                    if 'training_mae' in metadata:
                        self.training_mae = metadata['training_mae']
                print("✅ Successfully loaded ML models from root directory")
            else:
                print("⚠️ No existing models found, will use rule-based valuation")
                missing_files = [f for f in model_files if not os.path.exists(f)]
                print(f"⚠️ Missing files: {missing_files}")
        except Exception as e:
            print(f"⚠️ Error loading models: {e}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")

    def predict(self, property_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main prediction method for the orchestration agent
        """
        try:
            print(f"🔮 Starting property valuation prediction...")
            
            # Prepare property data for prediction
            property_data = {
                'city': str(property_details.get('city', '')),
                'area': str(property_details.get('area', '')),
                'property_type': str(property_details.get('property_type', '')),
                'size_sqft': float(property_details.get('size_sqft', 0)),
                'age_years': int(property_details.get('age_years', 0)),
                'floor_number': int(property_details.get('floor_number', 0)),
                'condition': str(property_details.get('condition', '')),
                'amenities': str(property_details.get('amenities', ''))
            }
            
            print(f"📊 Property Data Prepared for Prediction:")
            print(f"   City: {property_data['city']}")
            print(f"   Area: {property_data['area']}")
            print(f"   Type: {property_data['property_type']}")
            print(f"   Size: {property_data['size_sqft']} sq ft")
            print(f"   Age: {property_data['age_years']} years")
            print(f"   Condition: {property_data['condition']}")
            
            # Perform prediction
            result = self.predict_property_value(property_data)
            
            print(f"✅ Prediction completed successfully!")
            print(f"   Estimated Value: ₹{result['estimated_property_value']:,.2f}")
            print(f"   Price per sq ft: ₹{result['price_per_sqft']:,.2f}")
            print(f"   Confidence: {result['confidence_score']:.2%}")
            
            return {
                "status": "success",
                "estimated_property_value": result["estimated_property_value"],
                "price_per_sqft": result["price_per_sqft"],
                "confidence_score": result["confidence_score"],
                "valuation_method": result["valuation_method"],
                "model_accuracy": result.get("model_accuracy"),
                "property_data": property_data  # Include the data used for prediction
            }
            
        except Exception as e:
            print(f"❌ Property valuation prediction failed: {str(e)}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Property valuation failed: {str(e)}"
            }

    def predict_from_token(self, token: str) -> Dict[str, Any]:
        """
        Fetch application data from S3 using token and perform property valuation
        """
        try:
            # Fetch application data from S3 using token
            application_data = self.fetch_application_by_token(token)
            if not application_data:
                return {
                    "status": "error",
                    "message": f"No application data found for token: {token}"
                }
            
            # Convert raw form data to property_details structure
            property_details = {
                'size_sqft': float(application_data.get('property_size_sqft', 0)),
                'property_type': application_data.get('property_type', ''),
                'city': application_data.get('property_location_city', ''),
                'area': application_data.get('property_location_area', ''),
                'age_years': int(application_data.get('property_age_years', 0)),
                'condition': application_data.get('property_condition', ''),
                'amenities': application_data.get('amenities', '')
            }
            
            print(f"🏠 Property Details Extracted:")
            print(f"   Size: {property_details['size_sqft']} sq ft")
            print(f"   Type: {property_details['property_type']}")
            print(f"   City: {property_details['city']}")
            print(f"   Area: {property_details['area']}")
            print(f"   Age: {property_details['age_years']} years")
            print(f"   Condition: {property_details['condition']}")
            
            if not property_details.get('size_sqft') or not property_details.get('city'):
                return {
                    "status": "error",
                    "message": "Incomplete property details found in application data"
                }
            
            # Perform prediction
            result = self.predict(property_details)
            
            # Add application data to result
            result["application_data"] = application_data
            result["token"] = token
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Property valuation from token failed: {str(e)}"
            }

    def try_load_latest_model(self):
        try:
            saved_models = self.list_saved_models()
            if saved_models:
                default_model_name = "property_valuation_model"
                model_files = [m for m in saved_models if m['name'].startswith(default_model_name)]
                if model_files:
                    required_files = [
                        f"{default_model_name}.pkl",
                        f"{default_model_name}_scaler.pkl",
                        f"{default_model_name}_encoders.pkl"
                    ]
                    existing_files = [m['name'] for m in model_files]
                    if all(file in existing_files for file in required_files):
                        if self.load_models_from_pkl(default_model_name):
                            return True
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
            else:
                return False
        except Exception:
            return False

    def save_models_to_pkl(self, model_name: str = "property_valuation_model"):
        try:
            if not self.is_model_trained or self.model is None:
                return False
            model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            scaler_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            encoders_path = os.path.join(self.models_dir, f"{model_name}_encoders.pkl")
            with open(encoders_path, 'wb') as f:
                pickle.dump(self.label_encoders, f)
            metadata = {
                'is_model_trained': self.is_model_trained,
                'training_accuracy': getattr(self, 'training_accuracy', None),
                'training_mae': getattr(self, 'training_mae', None),
                'model_name': model_name,
                'saved_at': datetime.now().isoformat()
            }
            metadata_path = os.path.join(self.models_dir, f"{model_name}_metadata.pkl")
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            return True
        except Exception:
            return False

    def load_models_from_pkl(self, model_name: str = "property_valuation_model"):
        try:
            model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            if not os.path.exists(model_path):
                return False
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            scaler_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            encoders_path = os.path.join(self.models_dir, f"{model_name}_encoders.pkl")
            if os.path.exists(encoders_path):
                with open(encoders_path, 'rb') as f:
                    self.label_encoders = pickle.load(f)
            metadata_path = os.path.join(self.models_dir, f"{model_name}_metadata.pkl")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                    self.is_model_trained = metadata.get('is_model_trained', True)
                    if 'training_accuracy' in metadata:
                        self.training_accuracy = metadata['training_accuracy']
                    if 'training_mae' in metadata:
                        self.training_mae = metadata['training_mae']
            return True
        except Exception:
            return False

    def list_saved_models(self):
        try:
            if not os.path.exists(self.models_dir):
                return []
            model_files = []
            for file in os.listdir(self.models_dir):
                if file.endswith('.pkl'):
                    file_path = os.path.join(self.models_dir, file)
                    file_size = os.path.getsize(file_path)
                    model_files.append({
                        'name': file,
                        'size': file_size,
                        'path': file_path
                    })
            return model_files
        except Exception:
            return []

    def delete_saved_model(self, model_name: str):
        try:
            files_to_delete = [
                f"{model_name}.pkl",
                f"{model_name}_scaler.pkl", 
                f"{model_name}_encoders.pkl",
                f"{model_name}_metadata.pkl"
            ]
            for file in files_to_delete:
                file_path = os.path.join(self.models_dir, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
            return True
        except Exception:
            return False

    def save_models_to_s3(self, model_name: str = "property_valuation_model"):
        try:
            if not self.is_model_trained or self.model is None:
                return False
            model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            if os.path.exists(model_path):
                s3_key = f"ml_models/{model_name}.pkl"
                self.s3.upload_file(model_path, self.bucket_name, s3_key)
            scaler_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
            if os.path.exists(scaler_path):
                s3_key = f"ml_models/{model_name}_scaler.pkl"
                self.s3.upload_file(scaler_path, self.bucket_name, s3_key)
            encoders_path = os.path.join(self.models_dir, f"{model_name}_encoders.pkl")
            if os.path.exists(encoders_path):
                s3_key = f"ml_models/{model_name}_encoders.pkl"
                self.s3.upload_file(encoders_path, self.bucket_name, s3_key)
            metadata_path = os.path.join(self.models_dir, f"{model_name}_metadata.pkl")
            if os.path.exists(metadata_path):
                s3_key = f"ml_models/{model_name}_metadata.pkl"
                self.s3.upload_file(metadata_path, self.bucket_name, s3_key)
            return True
        except Exception:
            return False

    def load_models_from_s3(self, model_name: str = "property_valuation_model"):
        try:
            s3_key = f"ml_models/{model_name}.pkl"
            local_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            self.s3.download_file(self.bucket_name, s3_key, local_path)
            with open(local_path, 'rb') as f:
                self.model = pickle.load(f)
            scaler_s3_key = f"ml_models/{model_name}_scaler.pkl"
            scaler_local_path = os.path.join(self.models_dir, f"{model_name}_scaler.pkl")
            self.s3.download_file(self.bucket_name, scaler_s3_key, scaler_local_path)
            with open(scaler_local_path, 'rb') as f:
                self.scaler = pickle.load(f)
            encoders_s3_key = f"ml_models/{model_name}_encoders.pkl"
            encoders_local_path = os.path.join(self.models_dir, f"{model_name}_encoders.pkl")
            self.s3.download_file(self.bucket_name, encoders_s3_key, encoders_local_path)
            with open(encoders_local_path, 'rb') as f:
                self.label_encoders = pickle.load(f)
            metadata_s3_key = f"ml_models/{model_name}_metadata.pkl"
            metadata_local_path = os.path.join(self.models_dir, f"{model_name}_metadata.pkl")
            self.s3.download_file(self.bucket_name, metadata_s3_key, metadata_local_path)
            with open(metadata_local_path, 'rb') as f:
                metadata = pickle.load(f)
                self.is_model_trained = metadata.get('is_model_trained', True)
                if 'training_accuracy' in metadata:
                    self.training_accuracy = metadata['training_accuracy']
                if 'training_mae' in metadata:
                    self.training_mae = metadata['training_mae']
            return True
        except Exception:
            return False

    def fetch_latest_application(self) -> Optional[Dict]:
        """Fetch the most recent application from S3"""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="customers_data/"
            )
            
            if 'Contents' not in response:
                return None
            
            # Get the most recent application (excluding training data)
            applications = []
            for obj in response['Contents']:
                if obj['Key'].endswith('.json') and 'ml_training_' not in obj['Key']:
                    file_response = self.s3.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    application_data = json.loads(file_response['Body'].read())
                    
                    # Check if it has property valuation fields
                    if application_data.get('property_location_city') and application_data.get('property_type'):
                        applications.append({
                            'key': obj['Key'],
                            'data': application_data,
                            'last_modified': obj['LastModified']
                        })
            
            if not applications:
                return None
            
            # Get the most recent application
            latest_app = max(applications, key=lambda x: x['last_modified'])
            return latest_app['data']
            
        except Exception as e:
            print(f"Error fetching application from S3: {str(e)}")
            return None

    def fetch_application_by_token(self, token: str) -> Optional[Dict]:
        """Fetch application data from S3 using specific token"""
        try:
            # Construct the S3 key for the application using the correct structure
            application_key = f"customers_data/{token}/{token}_basic_info.json"
            
            print(f"🔍 Fetching from S3: Bucket={self.bucket_name}, Key={application_key}")
            
            # Fetch the application data
            response = self.s3.get_object(Bucket=self.bucket_name, Key=application_key)
            
            # Debug response details
            print(f"📊 Response Status: {response['ResponseMetadata']['HTTPStatusCode']}")
            print(f"📊 Content Length: {response.get('ContentLength', 'N/A')}")
            print(f"📊 Content Type: {response.get('ContentType', 'N/A')}")
            print(f"📊 ETag: {response.get('ETag', 'N/A')}")
            
            # Read the body content
            body_content = response['Body'].read()
            print(f"📊 Body Content Length: {len(body_content)} bytes")
            print(f"📊 Body Content Preview: {body_content[:200]}...")
            
            # Decode and parse JSON
            application_data = json.loads(body_content.decode('utf-8'))
            print(f"✅ Successfully parsed JSON with {len(application_data)} keys")
            print(f"📋 Available keys: {list(application_data.keys())}")
            
            return application_data
            
        except Exception as e:
            print(f"❌ Error fetching application for token {token}: {e}")
            print(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return None

    def fetch_training_data(self) -> List[Dict]:
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="customers_data/"
            )
            training_data = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.json') and ('ml_training_' in obj['Key'] or 
                                                       json.loads(self.s3.get_object(Bucket=self.bucket_name, Key=obj['Key'])['Body'].read()).get('source') == 'ml_training_data'):
                        file_response = self.s3.get_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        training_data.append(json.loads(file_response['Body'].read()))
            return training_data
        except Exception:
            return []

    def prepare_training_data(self, applications: List[Dict]) -> pd.DataFrame:
        training_data = []
        for app in applications:
            try:
                property_data = {
                    'city': str(app.get('property_location_city', '')).strip(),
                    'area': str(app.get('property_location_area', '')).strip(),
                    'property_type': str(app.get('property_type', '')).strip(),
                    'size_sqft': float(app.get('property_size_sqft', 0)),
                    'age_years': int(app.get('property_age_years', 0)),
                    'floor_number': int(app.get('floor_number', 0)),
                    'condition': str(app.get('property_condition', '')).strip(),
                    'amenities': str(app.get('amenities', '')).strip(),
                    'actual_value': float(app.get('estimated_property_value', 0))
                }
                if property_data['actual_value'] > 0 and property_data['size_sqft'] > 0:
                    training_data.append(property_data)
            except (ValueError, TypeError):
                continue
        return pd.DataFrame(training_data)

    def train_ml_model(self, df: pd.DataFrame):
        if len(df) < 5:
            return False
        try:
            feature_columns = ['city', 'area', 'property_type', 'size_sqft', 'age_years', 
                             'floor_number', 'condition', 'amenities']
            X = df[feature_columns].copy()
            y = df['actual_value']
            X = X.fillna('Unknown')
            for col in ['city', 'area', 'property_type', 'condition', 'amenities']:
                if col in X.columns:
                    le = LabelEncoder()
                    unique_values = X[col].unique()
                    le.fit(list(unique_values) + ['Unknown'])
                    X[col] = le.transform(X[col])
                    self.label_encoders[col] = le
            numerical_cols = ['size_sqft', 'age_years', 'floor_number']
            self.scaler = StandardScaler()
            X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])
            self.model = RandomForestRegressor(
                n_estimators=200, 
                random_state=42,
                max_depth=10,
                min_samples_split=5
            )
            self.model.fit(X, y)
            y_pred = self.model.predict(X)
            mae = mean_absolute_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            self.is_model_trained = True
            self.training_accuracy = r2
            self.training_mae = mae
            return True
        except Exception:
            return False

    def predict_property_value(self, property_data: Dict) -> Dict:
        try:
            print(f"🤖 ML Model Status Check:")
            print(f"   Model Trained: {self.is_model_trained}")
            print(f"   Model Object: {self.model is not None}")
            print(f"   Scaler Object: {self.scaler is not None}")
            print(f"   Label Encoders: {len(self.label_encoders) if self.label_encoders else 0}")
            
            if self.is_model_trained and self.model is not None and self.scaler is not None:
                print(f"✅ Using ML Model for prediction...")
                features = self.prepare_features_for_prediction(property_data)
                print(f"📊 Prepared Features: {features}")
                predicted_value = self.model.predict([features])[0]
                print(f"🎯 ML Predicted Value: ₹{predicted_value:,.2f}")
                confidence_score = self.calculate_ml_confidence(property_data)
                return {
                    "estimated_property_value": int(predicted_value),
                    "price_per_sqft": int(predicted_value / float(property_data.get('size_sqft', 1))),
                    "confidence_score": confidence_score,
                    "valuation_method": "ML Model",
                    "model_accuracy": self.get_model_accuracy()
                }
            else:
                print(f"⚠️ Falling back to Rule-Based valuation...")
                return self.rule_based_valuation(property_data)
        except Exception as e:
            print(f"❌ ML Model prediction failed: {str(e)}")
            print(f"⚠️ Falling back to Rule-Based valuation...")
            return self.rule_based_valuation(property_data)

    def prepare_features_for_prediction(self, property_data: Dict) -> List:
        features = []
        for col in ['city', 'area', 'property_type', 'condition', 'amenities']:
            if col in self.label_encoders:
                value = property_data.get(col, '')
                try:
                    encoded_value = self.label_encoders[col].transform([str(value)])[0]
                except:
                    encoded_value = 0
                features.append(encoded_value)
            else:
                features.append(0)
        numerical_features = [
            float(property_data.get('size_sqft', 0)),
            int(property_data.get('age_years', 0)),
            int(property_data.get('floor_number', 0))
        ]
        if self.scaler:
            numerical_features = self.scaler.transform([numerical_features])[0]
        features.extend(numerical_features)
        return features

    def calculate_ml_confidence(self, property_data: Dict) -> float:
        confidence = 0.8
        size_sqft = float(property_data.get('size_sqft', 0))
        if size_sqft > 0:
            confidence += 0.1
        if property_data.get('city') and property_data.get('area'):
            confidence += 0.05
        return min(confidence, 0.95)

    def get_model_accuracy(self) -> float:
        if hasattr(self, 'training_accuracy'):
            return self.training_accuracy
        return 0.85

    def rule_based_valuation(self, property_data: Dict) -> Dict:
        city_prices = {
            'mumbai': 20000, 'delhi': 15000, 'bangalore': 12000, 'hyderabad': 10000,
            'chennai': 9000, 'pune': 8000, 'rajahmundry': 5000, 'default': 10000
        }
        city = property_data.get('city', '').lower()
        base_price = city_prices.get(city, city_prices['default'])
        type_multipliers = {
            'apartment': 1.0, 'villa': 1.5, 'plot': 0.7, 'penthouse': 2.0, 'studio': 0.8
        }
        property_type = property_data.get('property_type', '').lower()
        type_multiplier = type_multipliers.get(property_type, 1.0)
        try:
            size_sqft = float(property_data.get('size_sqft', 1000))
            age_years = int(property_data.get('age_years', 0))
            floor_number = int(property_data.get('floor_number', 0))
        except (ValueError, TypeError):
            size_sqft = 1000
            age_years = 0
            floor_number = 0
        age_adjustment = max(0.7, 1.0 - (age_years * 0.01))
        floor_adjustment = 1.0 + (floor_number * 0.02) if floor_number > 0 else 0.9
        estimated_value = base_price * size_sqft * type_multiplier * age_adjustment * floor_adjustment
        return {
            "estimated_property_value": int(estimated_value),
            "price_per_sqft": int(estimated_value / size_sqft),
            "confidence_score": 0.75,
            "valuation_method": "Rule-Based",
            "model_accuracy": None
        }

    def save_valuation_result(self, application_id: str, valuation_result: Dict):
        try:
            key = f"property_valuations/{application_id}_valuation.json"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(valuation_result),
                ContentType="application/json"
            )
            return {"s3_key": key}
        except Exception:
            return None 