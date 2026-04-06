#!/usr/bin/env python3
"""
SCOI Backend API Testing Suite
Tests all backend endpoints for the SA Corruption OSINT Investigator platform
"""

import requests
import sys
import json
from datetime import datetime

class SCOIAPITester:
    def __init__(self, base_url="https://entity-resolver-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_token = None
        self.investigator_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.entity_ids = []  # Store entity IDs for testing

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def test_health_check(self):
        """Test backend health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Service: {data.get('service', 'Unknown')}"
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_admin_login(self):
        """Test admin login"""
        try:
            login_data = {
                "email": "admin@scoi.gov.za",
                "password": "SCOI2026!Admin"
            }
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                timeout=10
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Role: {data.get('role', 'Unknown')}"
                # Store cookies for future requests
                self.admin_token = True  # Using session cookies
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Admin Login", success, details)
            return success
        except Exception as e:
            self.log_test("Admin Login", False, str(e))
            return False

    def test_investigator_login(self):
        """Test investigator login with separate session"""
        try:
            # Create separate session for investigator
            inv_session = requests.Session()
            login_data = {
                "email": "investigator@scoi.gov.za", 
                "password": "Investigator2026!"
            }
            response = inv_session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                timeout=10
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Role: {data.get('role', 'Unknown')}"
                
            self.log_test("Investigator Login", success, details)
            return success
        except Exception as e:
            self.log_test("Investigator Login", False, str(e))
            return False

    def test_auth_me(self):
        """Test getting current user info"""
        try:
            response = self.session.get(f"{self.base_url}/api/auth/me", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", User: {data.get('email', 'Unknown')}"
                
            self.log_test("Auth Me", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Me", False, str(e))
            return False

    def test_entity_search_mokwena(self):
        """Test entity search for 'Mokwena'"""
        try:
            search_data = {
                "query": "Mokwena",
                "fuzzy": True,
                "limit": 10
            }
            response = self.session.post(
                f"{self.base_url}/api/entities/search",
                json=search_data,
                timeout=10
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                results_count = len(data)
                details += f", Results: {results_count}"
                
                # Store entity IDs for later tests
                for entity in data:
                    if entity.get('id'):
                        self.entity_ids.append(entity['id'])
                        
                # Check if we found Mokwena
                mokwena_found = any('mokwena' in entity.get('raw_name', '').lower() for entity in data)
                if mokwena_found:
                    details += ", Found Mokwena ✓"
                else:
                    details += ", Mokwena not found"
                    success = False
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Entity Search - Mokwena", success, details)
            return success
        except Exception as e:
            self.log_test("Entity Search - Mokwena", False, str(e))
            return False

    def test_entity_search_ndlovu(self):
        """Test entity search for 'Ndlovu'"""
        try:
            search_data = {
                "query": "Ndlovu",
                "fuzzy": True,
                "limit": 10
            }
            response = self.session.post(
                f"{self.base_url}/api/entities/search",
                json=search_data,
                timeout=10
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                results_count = len(data)
                details += f", Results: {results_count}"
                
                # Store entity IDs for later tests
                for entity in data:
                    if entity.get('id'):
                        self.entity_ids.append(entity['id'])
                        
                # Check if we found Ndlovu
                ndlovu_found = any('ndlovu' in entity.get('raw_name', '').lower() for entity in data)
                if ndlovu_found:
                    details += ", Found Ndlovu ✓"
                else:
                    details += ", Ndlovu not found"
                    success = False
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Entity Search - Ndlovu", success, details)
            return success
        except Exception as e:
            self.log_test("Entity Search - Ndlovu", False, str(e))
            return False

    def test_entity_graph(self):
        """Test network graph generation"""
        if not self.entity_ids:
            self.log_test("Network Graph", False, "No entity IDs available")
            return False
            
        try:
            entity_id = self.entity_ids[0]
            response = self.session.get(
                f"{self.base_url}/api/entities/graph/{entity_id}?hops=2",
                timeout=15
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                nodes_count = len(data.get('nodes', []))
                edges_count = len(data.get('edges', []))
                details += f", Nodes: {nodes_count}, Edges: {edges_count}"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Network Graph", success, details)
            return success
        except Exception as e:
            self.log_test("Network Graph", False, str(e))
            return False

    def test_asset_tracing(self):
        """Test asset tracing functionality"""
        if not self.entity_ids:
            self.log_test("Asset Tracing", False, "No entity IDs available")
            return False
            
        try:
            # Find a person entity for asset tracing
            person_id = None
            for entity_id in self.entity_ids:
                # Get entity details to check if it's a person
                response = self.session.get(f"{self.base_url}/api/entities/{entity_id}", timeout=10)
                if response.status_code == 200:
                    entity = response.json()
                    if entity.get('type') == 'person':
                        person_id = entity_id
                        break
            
            if not person_id:
                self.log_test("Asset Tracing", False, "No person entity found")
                return False
                
            response = self.session.get(
                f"{self.base_url}/api/assets/trace/{person_id}",
                timeout=15
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                total_assets = data.get('total_assets', 0)
                total_value = data.get('total_estimated_value', 0)
                details += f", Assets: {total_assets}, Value: R{total_value:,.0f}" if total_value else f", Assets: {total_assets}"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Asset Tracing", success, details)
            return success
        except Exception as e:
            self.log_test("Asset Tracing", False, str(e))
            return False

    def test_red_flags(self):
        """Test red flag evaluation"""
        if not self.entity_ids:
            self.log_test("Red Flag Evaluation", False, "No entity IDs available")
            return False
            
        try:
            entity_id = self.entity_ids[0]
            response = self.session.post(
                f"{self.base_url}/api/entities/rules/evaluate?entity_id={entity_id}",
                timeout=15
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                matches_count = len(data.get('matches', []))
                details += f", Red Flags: {matches_count}"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Red Flag Evaluation", success, details)
            return success
        except Exception as e:
            self.log_test("Red Flag Evaluation", False, str(e))
            return False

    def test_create_entity(self):
        """Test entity creation (admin only)"""
        try:
            entity_data = {
                "type": "person",
                "raw_name": "Test Person for API Testing",
                "source": "API Test",
                "source_url": "https://test.example.com",
                "metadata": {
                    "dob_year": 1990,
                    "roles": ["Test Subject"]
                }
            }
            response = self.session.post(
                f"{self.base_url}/api/entities/",
                json=entity_data,
                timeout=10
            )
            success = response.status_code == 201
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Created ID: {data.get('id', 'Unknown')[:8]}..."
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Create Entity", success, details)
            return success
        except Exception as e:
            self.log_test("Create Entity", False, str(e))
            return False

    def test_audit_logs(self):
        """Test audit logs access (admin only)"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/audit/logs?limit=10",
                timeout=10
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                logs_count = len(data)
                details += f", Logs: {logs_count}"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Audit Logs", success, details)
            return success
        except Exception as e:
            self.log_test("Audit Logs", False, str(e))
            return False

    def test_report_generation(self):
        """Test LLM report generation"""
        if not self.entity_ids:
            self.log_test("Report Generation", False, "No entity IDs available")
            return False
            
        try:
            report_data = {
                "title": "API Test Investigation Report",
                "entity_ids": self.entity_ids[:2],  # Use first 2 entities
                "include_graph": True,
                "include_red_flags": True
            }
            response = self.session.post(
                f"{self.base_url}/api/entities/reports/generate",
                json=report_data,
                timeout=30  # LLM calls can be slow
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                content_length = len(data.get('content', ''))
                details += f", Report Length: {content_length} chars"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Report Generation", success, details)
            return success
        except Exception as e:
            self.log_test("Report Generation", False, str(e))
            return False

    def test_watchlist_get(self):
        """Test getting watchlist"""
        try:
            response = self.session.get(f"{self.base_url}/api/watchlist/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                items_count = len(data.get('items', []))
                details += f", Watchlist Items: {items_count}"
                
                # Check if we have the expected seeded entities (Mokwena + Mbokodo)
                if items_count >= 2:
                    details += " (Expected seeded entities found)"
                else:
                    details += " (Warning: Expected 2+ seeded entities)"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Watchlist Get", success, details)
            return success
        except Exception as e:
            self.log_test("Watchlist Get", False, str(e))
            return False

    def test_watchlist_alerts(self):
        """Test getting watchlist alerts"""
        try:
            response = self.session.get(f"{self.base_url}/api/watchlist/alerts?limit=50", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                alerts_count = len(data.get('alerts', []))
                details += f", Alerts: {alerts_count}"
                
                # Check if we have active alerts
                if alerts_count > 0:
                    details += " (Active alerts found)"
                    # Check alert structure
                    first_alert = data['alerts'][0]
                    if all(key in first_alert for key in ['id', 'entity_name', 'alert_type', 'severity']):
                        details += " ✓"
                else:
                    details += " (No alerts - may be expected)"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Watchlist Alerts", success, details)
            return success
        except Exception as e:
            self.log_test("Watchlist Alerts", False, str(e))
            return False

    def test_watchlist_add(self):
        """Test adding entity to watchlist"""
        if not self.entity_ids:
            self.log_test("Watchlist Add", False, "No entity IDs available")
            return False
            
        try:
            # Use the first available entity ID
            entity_id = self.entity_ids[0]
            add_data = {
                "entity_id": entity_id,
                "notes": "API Test - Added via backend test"
            }
            response = self.session.post(
                f"{self.base_url}/api/watchlist/add",
                json=add_data,
                timeout=15
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Added: {data.get('entity_name', 'Unknown')}"
                alerts_generated = data.get('alerts_generated', 0)
                details += f", Alerts Generated: {alerts_generated}"
            else:
                details += f", Response: {response.text[:100]}"
                # If entity already on watchlist, that's also acceptable
                if response.status_code == 400 and "already on watchlist" in response.text:
                    success = True
                    details = "Status: 400 (Entity already on watchlist - acceptable)"
                
            self.log_test("Watchlist Add", success, details)
            return success
        except Exception as e:
            self.log_test("Watchlist Add", False, str(e))
            return False

    def test_watchlist_scan(self):
        """Test watchlist scan functionality"""
        try:
            response = self.session.post(f"{self.base_url}/api/watchlist/scan", json={}, timeout=20)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                message = data.get('message', '')
                details += f", Result: {message}"
            else:
                details += f", Response: {response.text[:100]}"
                
            self.log_test("Watchlist Scan", success, details)
            return success
        except Exception as e:
            self.log_test("Watchlist Scan", False, str(e))
            return False

    def test_logout(self):
        """Test logout functionality"""
        try:
            response = self.session.post(f"{self.base_url}/api/auth/logout", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'Unknown')}"
                
            self.log_test("Logout", success, details)
            return success
        except Exception as e:
            self.log_test("Logout", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🔍 SCOI Backend API Testing Suite")
        print("=" * 50)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Backend not accessible, stopping tests")
            return False
            
        # Authentication tests
        if not self.test_admin_login():
            print("❌ Admin login failed, stopping tests")
            return False
            
        self.test_investigator_login()
        self.test_auth_me()
        
        # Core functionality tests
        self.test_entity_search_mokwena()
        self.test_entity_search_ndlovu()
        self.test_entity_graph()
        self.test_asset_tracing()
        self.test_red_flags()
        
        # NEW: Watchlist/Alert system tests
        print("\n👁️ Testing Watchlist/Alert System...")
        self.test_watchlist_get()
        self.test_watchlist_alerts()
        self.test_watchlist_add()
        self.test_watchlist_scan()
        
        # Admin functionality tests
        self.test_create_entity()
        self.test_audit_logs()
        
        # LLM functionality (may be slow)
        print("\n🤖 Testing LLM Integration (may take 10-30 seconds)...")
        self.test_report_generation()
        
        # Cleanup
        self.test_logout()
        
        # Results
        print("\n" + "=" * 50)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = SCOIAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())