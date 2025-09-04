import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId

# ------------------ MongoDB Connection ------------------
# Replace with your own MongoDB connection string
client = MongoClient("mongodb+srv://deosanika001_db_user:lolSju3x8UIkxovW@cluster0.oqus1qt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["notes_db"]
notes_collection = db["notes"]

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="Notes App", page_icon="📝", layout="centered")
st.title("📝 Atharva Notes App")

menu = ["Create", "Read", "Update", "Delete", "Search"]
choice = st.sidebar.selectbox("Menu", menu)

# ------------------ CREATE ------------------
if choice == "Create":
    st.subheader("➕ Add New Note")
    title = st.text_input("Title")
    content = st.text_area("Content")
    if st.button("Save"):
        if title and content:
            notes_collection.insert_one({"title": title, "content": content})
            st.success("✅ Note added successfully!")
        else:
            st.warning("⚠️ Please enter both title and content.")

# ------------------ READ ------------------
elif choice == "Read":
    st.subheader("📖 All Notes")
    notes = list(notes_collection.find())
    if notes:
        for note in notes:
            st.markdown(f"**{note['title']}**")
            st.write(note["content"])
            st.markdown("---")
    else:
        st.info("No notes available.")

# ------------------ UPDATE ------------------
elif choice == "Update":
    st.subheader("✏️ Update a Note")
    notes = list(notes_collection.find())
    note_titles = [note["title"] for note in notes]
    selected = st.selectbox("Select a note to update", note_titles)

    note = notes_collection.find_one({"title": selected})
    new_title = st.text_input("New Title", value=note["title"])
    new_content = st.text_area("New Content", value=note["content"])

    if st.button("Update"):
        notes_collection.update_one(
            {"_id": note["_id"]},
            {"$set": {"title": new_title, "content": new_content}},
        )
        st.success("✅ Note updated successfully!")

# ------------------ DELETE ------------------
elif choice == "Delete":
    st.subheader("🗑️ Delete a Note")
    notes = list(notes_collection.find())
    note_titles = [note["title"] for note in notes]
    selected = st.selectbox("Select a note to delete", note_titles)

    if st.button("Delete"):
        notes_collection.delete_one({"title": selected})
        st.success("🗑️ Note deleted successfully!")

# ------------------ SEARCH ------------------
elif choice == "Search":
    st.subheader("🔍 Search Notes")
    query = st.text_input("Enter keyword")
    if st.button("Search"):
        results = list(
            notes_collection.find(
                {"$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}}
                ]}
            )
        )
        if results:
            st.write(f"Found {len(results)} note(s):")
            for note in results:
                st.markdown(f"**{note['title']}**")
                st.write(note["content"])
                st.markdown("---")
        else:
            st.warning("No matching notes found.")

