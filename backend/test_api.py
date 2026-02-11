"""
API Test Script for IPO Platform
Tests all CRUD operations and filters
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    if response.status_code < 400:
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")


def test_health_check():
    """Test health check endpoint"""
    response = requests.get("http://localhost:8000/health")
    print_response("Health Check", response)
    return response.status_code == 200


def test_create_ipo():
    """Test creating a new IPO"""
    ipo_data = {
        "company_name": "Test Innovations Ltd",
        "symbol": "TESTINN",
        "status": "upcoming",
        "ipo_type": "mainboard",
        "open_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "close_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "price_band_lower": 150.0,
        "price_band_upper": 160.0,
        "issue_size_rs_cr": 800.0,
        "industry_sector": "Technology",
        "lot_size": 90,
        "description": "Test company for API testing"
    }
    
    response = requests.post(
        f"{BASE_URL}/ipos/",
        headers=HEADERS,
        json=ipo_data
    )
    print_response("Create IPO", response)
    
    if response.status_code == 201:
        return response.json()["id"]
    return None


def test_get_all_ipos():
    """Test getting all IPOs with pagination"""
    response = requests.get(f"{BASE_URL}/ipos/?page=1&page_size=5")
    print_response("Get All IPOs (Paginated)", response)


def test_get_ipo_by_id(ipo_id):
    """Test getting specific IPO by ID"""
    response = requests.get(f"{BASE_URL}/ipos/{ipo_id}")
    print_response(f"Get IPO by ID ({ipo_id})", response)


def test_get_ipo_by_symbol():
    """Test getting IPO by symbol"""
    response = requests.get(f"{BASE_URL}/ipos/symbol/TECHVIS")
    print_response("Get IPO by Symbol (TECHVIS)", response)


def test_update_ipo(ipo_id):
    """Test updating an IPO"""
    update_data = {
        "total_subscription": 4.2,
        "qib_subscription": 5.1,
        "gmp_amount": 30.0,
        "gmp_percentage": 18.75
    }
    
    response = requests.put(
        f"{BASE_URL}/ipos/{ipo_id}",
        headers=HEADERS,
        json=update_data
    )
    print_response(f"Update IPO ({ipo_id})", response)


def test_get_active_ipos():
    """Test getting active IPOs"""
    response = requests.get(f"{BASE_URL}/ipos/active")
    print_response("Get Active IPOs", response)


def test_get_upcoming_ipos():
    """Test getting upcoming IPOs"""
    response = requests.get(f"{BASE_URL}/ipos/upcoming?limit=5")
    print_response("Get Upcoming IPOs", response)


def test_filter_by_status():
    """Test filtering by status"""
    response = requests.get(f"{BASE_URL}/ipos/?status=open&page_size=10")
    print_response("Filter by Status (OPEN)", response)


def test_filter_by_sector():
    """Test filtering by industry sector"""
    response = requests.get(f"{BASE_URL}/ipos/?industry_sector=Technology")
    print_response("Filter by Sector (Technology)", response)


def test_search():
    """Test search functionality"""
    response = requests.get(f"{BASE_URL}/ipos/?search=tech")
    print_response("Search IPOs (keyword: tech)", response)


def test_sort_by_subscription():
    """Test sorting by subscription"""
    response = requests.get(
        f"{BASE_URL}/ipos/?sort_by=total_subscription&sort_order=desc&page_size=5"
    )
    print_response("Sort by Subscription (Descending)", response)


def test_delete_ipo(ipo_id):
    """Test deleting an IPO"""
    response = requests.delete(f"{BASE_URL}/ipos/{ipo_id}")
    print_response(f"Delete IPO ({ipo_id})", response)


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("🚀 IPO PLATFORM API TEST SUITE")
    print("="*60)
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ Server is not running. Please start the server first.")
        return
    
    # Test 2: Create IPO
    print("\n📝 TESTING CREATE OPERATION")
    ipo_id = test_create_ipo()
    
    # Test 3: Read Operations
    print("\n📖 TESTING READ OPERATIONS")
    test_get_all_ipos()
    if ipo_id:
        test_get_ipo_by_id(ipo_id)
    test_get_ipo_by_symbol()
    test_get_active_ipos()
    test_get_upcoming_ipos()
    
    # Test 4: Update Operation
    print("\n✏️  TESTING UPDATE OPERATION")
    if ipo_id:
        test_update_ipo(ipo_id)
    
    # Test 5: Filter Operations
    print("\n🔍 TESTING FILTER & SEARCH")
    test_filter_by_status()
    test_filter_by_sector()
    test_search()
    test_sort_by_subscription()
    
    # Test 6: Delete Operation
    print("\n🗑️  TESTING DELETE OPERATION")
    if ipo_id:
        test_delete_ipo(ipo_id)
    
    print("\n" + "="*60)
    print("✅ TEST SUITE COMPLETED")
    print("="*60)


if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the server.")
        print("Please ensure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
