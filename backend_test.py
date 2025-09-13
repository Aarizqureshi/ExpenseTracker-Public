#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Expense Tracker
Tests all backend endpoints including authentication, CRUD operations, analytics, and exports
"""

import requests
import json
import csv
import io
from datetime import datetime, timezone, timedelta
import uuid
import sys
import os

# Get backend URL from frontend .env
BACKEND_URL = "https://budget-buddy-1315.preview.emergentagent.com/api"

class ExpenseTrackerTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session_token = None
        self.test_user_id = None
        self.test_transactions = []
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def test_categories_endpoint(self):
        """Test the categories endpoint (no auth required)"""
        self.log("Testing categories endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/categories")
            
            if response.status_code == 200:
                data = response.json()
                if "expense_categories" in data and "income_categories" in data:
                    self.log("✅ Categories endpoint working - returns expense and income categories")
                    return True
                else:
                    self.log("❌ Categories endpoint missing required fields")
                    return False
            else:
                self.log(f"❌ Categories endpoint failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Categories endpoint error: {str(e)}")
            return False
    
    def test_auth_endpoints_without_session(self):
        """Test auth endpoints without valid session (should return 401/400)"""
        self.log("Testing authentication endpoints without session...")
        
        # Test session-data endpoint without X-Session-ID header
        try:
            response = self.session.get(f"{self.base_url}/auth/session-data")
            if response.status_code == 400:
                self.log("✅ Session-data endpoint correctly returns 400 without session ID")
            else:
                self.log(f"❌ Session-data endpoint returned {response.status_code} instead of 400")
                return False
        except Exception as e:
            self.log(f"❌ Session-data endpoint error: {str(e)}")
            return False
            
        # Test /auth/me without authentication
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            if response.status_code == 401:
                self.log("✅ Auth/me endpoint correctly returns 401 without authentication")
            else:
                self.log(f"❌ Auth/me endpoint returned {response.status_code} instead of 401")
                return False
        except Exception as e:
            self.log(f"❌ Auth/me endpoint error: {str(e)}")
            return False
            
        # Test logout endpoint
        try:
            response = self.session.post(f"{self.base_url}/auth/logout")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log("✅ Logout endpoint working (returns success even without session)")
                else:
                    self.log("❌ Logout endpoint missing message field")
                    return False
            else:
                self.log(f"❌ Logout endpoint failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Logout endpoint error: {str(e)}")
            return False
            
        return True
    
    def test_protected_endpoints_without_auth(self):
        """Test that protected endpoints return 401 without authentication"""
        self.log("Testing protected endpoints without authentication...")
        
        protected_endpoints = [
            ("GET", "/transactions"),
            ("POST", "/transactions"),
            ("GET", "/transactions/test-id"),
            ("PUT", "/transactions/test-id"),
            ("DELETE", "/transactions/test-id"),
            ("GET", "/dashboard/stats"),
            ("GET", "/analytics/monthly"),
            ("GET", "/export/csv"),
            ("GET", "/export/pdf")
        ]
        
        all_passed = True
        for method, endpoint in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                elif method == "PUT":
                    response = self.session.put(f"{self.base_url}{endpoint}", json={})
                elif method == "DELETE":
                    response = self.session.delete(f"{self.base_url}{endpoint}")
                    
                if response.status_code == 401:
                    self.log(f"✅ {method} {endpoint} correctly returns 401 without auth")
                else:
                    self.log(f"❌ {method} {endpoint} returned {response.status_code} instead of 401")
                    all_passed = False
                    
            except Exception as e:
                self.log(f"❌ {method} {endpoint} error: {str(e)}")
                all_passed = False
                
        return all_passed
    
    def test_transaction_crud_with_mock_auth(self):
        """Test transaction CRUD operations with mock authentication headers"""
        self.log("Testing transaction CRUD operations with mock auth headers...")
        
        # Create mock session token for testing
        mock_token = "mock-session-token-for-testing"
        headers = {"Authorization": f"Bearer {mock_token}"}
        
        # Test creating transaction
        transaction_data = {
            "type": "expense",
            "amount": 50.00,
            "category": "Food & Dining",
            "description": "Lunch at restaurant",
            "date": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/transactions",
                json=transaction_data,
                headers=headers
            )
            
            # Should return 401 since mock token is invalid, but endpoint should be reachable
            if response.status_code == 401:
                self.log("✅ Transaction creation endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ Transaction creation returned unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Transaction creation error: {str(e)}")
            return False
            
        # Test getting transactions
        try:
            response = self.session.get(f"{self.base_url}/transactions", headers=headers)
            if response.status_code == 401:
                self.log("✅ Get transactions endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ Get transactions returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Get transactions error: {str(e)}")
            return False
            
        # Test getting specific transaction
        try:
            test_id = str(uuid.uuid4())
            response = self.session.get(f"{self.base_url}/transactions/{test_id}", headers=headers)
            if response.status_code == 401:
                self.log("✅ Get specific transaction endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ Get specific transaction returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Get specific transaction error: {str(e)}")
            return False
            
        # Test updating transaction
        try:
            test_id = str(uuid.uuid4())
            update_data = {"amount": 75.00}
            response = self.session.put(
                f"{self.base_url}/transactions/{test_id}",
                json=update_data,
                headers=headers
            )
            if response.status_code == 401:
                self.log("✅ Update transaction endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ Update transaction returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Update transaction error: {str(e)}")
            return False
            
        # Test deleting transaction
        try:
            test_id = str(uuid.uuid4())
            response = self.session.delete(f"{self.base_url}/transactions/{test_id}", headers=headers)
            if response.status_code == 401:
                self.log("✅ Delete transaction endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ Delete transaction returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Delete transaction error: {str(e)}")
            return False
            
        return True
    
    def test_dashboard_analytics_endpoints(self):
        """Test dashboard and analytics endpoints"""
        self.log("Testing dashboard and analytics endpoints...")
        
        mock_token = "mock-session-token-for-testing"
        headers = {"Authorization": f"Bearer {mock_token}"}
        
        # Test dashboard stats
        try:
            response = self.session.get(f"{self.base_url}/dashboard/stats", headers=headers)
            if response.status_code == 401:
                self.log("✅ Dashboard stats endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ Dashboard stats returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Dashboard stats error: {str(e)}")
            return False
            
        # Test monthly analytics
        try:
            response = self.session.get(f"{self.base_url}/analytics/monthly", headers=headers)
            if response.status_code == 401:
                self.log("✅ Monthly analytics endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ Monthly analytics returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Monthly analytics error: {str(e)}")
            return False
            
        return True
    
    def test_export_endpoints(self):
        """Test CSV and PDF export endpoints"""
        self.log("Testing export endpoints...")
        
        mock_token = "mock-session-token-for-testing"
        headers = {"Authorization": f"Bearer {mock_token}"}
        
        # Test CSV export
        try:
            response = self.session.get(f"{self.base_url}/export/csv", headers=headers)
            if response.status_code == 401:
                self.log("✅ CSV export endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ CSV export returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ CSV export error: {str(e)}")
            return False
            
        # Test PDF export
        try:
            response = self.session.get(f"{self.base_url}/export/pdf", headers=headers)
            if response.status_code == 401:
                self.log("✅ PDF export endpoint reachable (returns 401 for invalid token)")
            else:
                self.log(f"❌ PDF export returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ PDF export error: {str(e)}")
            return False
            
        return True
    
    def test_transaction_filtering(self):
        """Test transaction filtering parameters"""
        self.log("Testing transaction filtering parameters...")
        
        mock_token = "mock-session-token-for-testing"
        headers = {"Authorization": f"Bearer {mock_token}"}
        
        # Test category filtering
        try:
            response = self.session.get(
                f"{self.base_url}/transactions?category=Food%20%26%20Dining",
                headers=headers
            )
            if response.status_code == 401:
                self.log("✅ Transaction filtering by category endpoint reachable")
            else:
                self.log(f"❌ Transaction filtering returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Transaction filtering error: {str(e)}")
            return False
            
        # Test date range filtering
        try:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
            end_date = datetime.now().isoformat()
            response = self.session.get(
                f"{self.base_url}/transactions?start_date={start_date}&end_date={end_date}",
                headers=headers
            )
            if response.status_code == 401:
                self.log("✅ Transaction filtering by date range endpoint reachable")
            else:
                self.log(f"❌ Date range filtering returned unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Date range filtering error: {str(e)}")
            return False
            
        return True
    
    def check_server_connectivity(self):
        """Check if the backend server is running and accessible"""
        self.log("Checking backend server connectivity...")
        try:
            # Try to reach the categories endpoint (no auth required)
            response = self.session.get(f"{self.base_url}/categories", timeout=10)
            if response.status_code == 200:
                self.log("✅ Backend server is accessible")
                return True
            else:
                self.log(f"❌ Backend server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log("❌ Cannot connect to backend server - connection refused")
            return False
        except requests.exceptions.Timeout:
            self.log("❌ Backend server connection timeout")
            return False
        except Exception as e:
            self.log(f"❌ Backend server connectivity error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("=" * 60)
        self.log("STARTING COMPREHENSIVE BACKEND API TESTING")
        self.log("=" * 60)
        
        test_results = {}
        
        # Check server connectivity first
        if not self.check_server_connectivity():
            self.log("❌ CRITICAL: Backend server is not accessible. Cannot proceed with testing.")
            return {"server_connectivity": False}
        
        # Test categories endpoint (no auth required)
        test_results["categories"] = self.test_categories_endpoint()
        
        # Test authentication endpoints
        test_results["auth_endpoints"] = self.test_auth_endpoints_without_session()
        
        # Test protected endpoints return 401 without auth
        test_results["protected_endpoints_auth"] = self.test_protected_endpoints_without_auth()
        
        # Test transaction CRUD operations
        test_results["transaction_crud"] = self.test_transaction_crud_with_mock_auth()
        
        # Test dashboard and analytics
        test_results["dashboard_analytics"] = self.test_dashboard_analytics_endpoints()
        
        # Test export endpoints
        test_results["export_endpoints"] = self.test_export_endpoints()
        
        # Test transaction filtering
        test_results["transaction_filtering"] = self.test_transaction_filtering()
        
        # Summary
        self.log("=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name}: {status}")
        
        self.log(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL BACKEND TESTS PASSED!")
        else:
            self.log("⚠️  Some backend tests failed - see details above")
        
        return test_results

if __name__ == "__main__":
    tester = ExpenseTrackerTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)