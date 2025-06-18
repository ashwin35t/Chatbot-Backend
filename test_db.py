import asyncio
from mongodb import MongoDB
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

async def test_connection():
    try:
        # Connect to MongoDB
        await MongoDB.connect_to_database()
        print("Successfully connected to MongoDB!")
        
        # Test creating a collection
        collection = await MongoDB.get_collection("test_collection")
        print("Successfully accessed test collection!")
        
        # Test inserting a document
        test_doc = {"test": "Hello MongoDB!"}
        result = await collection.insert_one(test_doc)
        print(f"Successfully inserted test document with ID: {result.inserted_id}")
        
        # Test reading the document
        doc = await collection.find_one({"test": "Hello MongoDB!"})
        print(f"Successfully retrieved document: {doc}")
        
        # Clean up
        await collection.delete_one({"test": "Hello MongoDB!"})
        print("Successfully cleaned up test document")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Close the connection
        await MongoDB.close_database_connection()
        print("Closed MongoDB connection")

if __name__ == "__main__":
    asyncio.run(test_connection())

print(quote_plus("Xxaswi@100")) 