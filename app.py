# app.py
import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, List, Dict

# Example URI formats:
# - MongoDB Atlas (SRV): "mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/mydatabase?retryWrites=true&w=majority"
# - Local: "mongodb://localhost:27017"
MONGO_URI = "mongodb+srv://deosanika001_db_user:iffCWcxW0eLVQ6ES@cluster0.telweny.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "notesdb"
COLLECTION_NAME = "notes"

# -------------------------
# DB helper functions
# -------------------------
@st.cache_resource
def get_client(uri: str) -> MongoClient:
    return MongoClient(uri)

def get_collection(client: MongoClient):
    db = client[DB_NAME]
    return db[COLLECTION_NAME]

def create_note(collection, title: str, content: str, tags: Optional[List[str]] = None) -> str:
    doc = {
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    res = collection.insert_one(doc)
    return str(res.inserted_id)

def get_notes(collection, search: Optional[str] = None, tag_filter: Optional[str] = None, limit: int = 100) -> List[Dict]:
    q = {}
    if search:
        q["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
        ]
    if tag_filter:
        q["tags"] = tag_filter
    docs = collection.find(q).sort("updated_at", -1).limit(limit)
    result = []
    for d in docs:
        d["id"] = str(d["_id"])
        d.pop("_id", None)
        result.append(d)
    return result

def get_note_by_id(collection, note_id: str) -> Optional[Dict]:
    try:
        doc = collection.find_one({"_id": ObjectId(note_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc

def update_note(collection, note_id: str, title: str, content: str, tags: Optional[List[str]] = None) -> bool:
    try:
        res = collection.update_one(
            {"_id": ObjectId(note_id)},
            {"$set": {"title": title, "content": content, "tags": tags or [], "updated_at": datetime.utcnow()}}
        )
        return res.modified_count > 0
    except Exception:
        return False

def delete_note(collection, note_id: str) -> bool:
    try:
        res = collection.delete_one({"_id": ObjectId(note_id)})
        return res.deleted_count > 0
    except Exception:
        return False

# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="Atharva Notes App", page_icon="🗒️", layout="wide")
st.title("🗒️ Atharva Notes App ")

# Connect to DB
try:
    client = get_client(MONGO_URI)
    col = get_collection(client)
except Exception as e:
    st.error("Unable to connect to MongoDB. Check your MONGO_URI in the script.")
    st.exception(e)
    st.stop()

# Sidebar: controls
st.sidebar.header("Actions")
mode = st.sidebar.radio("Choose mode", ["Create note", "View / Edit notes", "Delete note", "Raw DB status"])

# Simple search & tag filter on top
with st.container():
    c1, c2 = st.columns([3,1])
    with c1:
        search_query = st.text_input("Search notes (title, content, tags)", value="")
    with c2:
        tag_filter = st.text_input("Filter by single tag (exact)", value="")

if mode == "Create note":
    st.subheader("Create a new note")
    with st.form("create_form", clear_on_submit=True):
        title = st.text_input("Title", max_chars=120)
        content = st.text_area("Content", height=200)
        tags_raw = st.text_input("Tags (comma-separated)", help="Optional, e.g. work,ideas")
        submitted = st.form_submit_button("Create")
        if submitted:
            if not title.strip():
                st.warning("Title can't be empty.")
            else:
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
                try:
                    new_id = create_note(col, title.strip(), content.strip(), tags)
                    st.success("Note created!")
                    st.write(f"ID: `{new_id}`")
                except Exception as e:
                    st.error("Failed to create note.")
                    st.exception(e)

elif mode == "View / Edit notes":
    st.subheader("Notes list — view or edit")
    notes = get_notes(col, search=search_query.strip() or None, tag_filter=tag_filter.strip() or None, limit=500)
    if not notes:
        st.info("No notes found. Create one from the sidebar or check your search/filter.")
    else:
        for n in notes:
            with st.expander(f"{n.get('title') or '(no title)'} — {n.get('id')}", expanded=False):
                st.write("**Content**")
                st.write(n.get("content") or "")
                if n.get("tags"):
                    st.write("**Tags:**", ", ".join(n.get("tags")))
                st.write("**Created:**", n.get("created_at"))
                st.write("**Updated:**", n.get("updated_at"))
                # Edit area
                if st.button("Edit this note", key=f"edit_btn_{n['id']}"):
                    st.session_state["edit_note_id"] = n["id"]
                    st.experimental_rerun()

        # If an edit is requested show editor
        if "edit_note_id" in st.session_state:
            edit_id = st.session_state["edit_note_id"]
            note = get_note_by_id(col, edit_id)
            if not note:
                st.error("Note not found (it may have been deleted).")
                st.session_state.pop("edit_note_id", None)
            else:
                st.markdown("---")
                st.subheader(f"Editing: {note['title']}")
                with st.form("edit_form"):
                    new_title = st.text_input("Title", value=note.get("title", ""))
                    new_content = st.text_area("Content", value=note.get("content", ""), height=200)
                    tags_string = st.text_input("Tags (comma-separated)", value=",".join(note.get("tags", [])))
                    save = st.form_submit_button("Save changes")
                    cancel = st.form_submit_button("Cancel")
                    if save:
                        tags = [t.strip() for t in tags_string.split(",") if t.strip()]
                        ok = update_note(col, edit_id, new_title.strip(), new_content.strip(), tags)
                        if ok:
                            st.success("Saved.")
                        else:
                            st.warning("No changes were made or update failed.")
                        st.session_state.pop("edit_note_id", None)
                        st.experimental_rerun()
                    if cancel:
                        st.session_state.pop("edit_note_id", None)
                        st.experimental_rerun()

elif mode == "Delete note":
    st.subheader("Delete notes")
    del_id = st.text_input("Enter note ID to delete (or choose from list below)", value="")
    if st.button("Delete by ID"):
        if not del_id.strip():
            st.warning("Provide an ID.")
        else:
            ok = delete_note(col, del_id.strip())
            if ok:
                st.success("Note deleted.")
            else:
                st.error("Delete failed — confirm the ID is correct.")
    st.markdown("### Or select from existing notes")
    notes = get_notes(col, search=search_query.strip() or None, tag_filter=tag_filter.strip() or None)
    if notes:
        ids = {n["id"]: f"{n['title'][:60]} ({n['id']})" for n in notes}
        selected = st.selectbox("Select note to delete", options=[""] + list(ids.keys()), format_func=lambda k: ids.get(k, "") if k else "")
        if selected:
            if st.button("Delete selected"):
                ok = delete_note(col, selected)
                if ok:
                    st.success("Deleted.")
                    st.experimental_rerun()
                else:
                    st.error("Delete failed.")

elif mode == "Raw DB status":
    st.subheader("Database status & quick actions")
    try:
        info = client.server_info()
        st.write("**MongoDB server info:**")
        st.json({
            "version": info.get("version"),
            "sysInfo": info.get("sysInfo") if "sysInfo" in info else "n/a",
        })
    except Exception as e:
        st.error("Couldn't fetch server info.")
        st.exception(e)

    st.markdown("---")
    st.write("Quick collection stats:")
    try:
        stats = client[DB_NAME].command("collstats", COLLECTION_NAME)
        st.json({
            "ns": stats.get("ns"),
            "count": stats.get("count"),
            "size_bytes": stats.get("size"),
            "storageSize": stats.get("storageSize"),
            "totalIndexSize": stats.get("totalIndexSize"),
        })
    except Exception as e:
        st.warning("Unable to get collstats (some Mongo providers restrict this).")
        st.exception(e)

    st.markdown("---")
    if st.button("Clear all notes (DROP collection)"):
        if st.confirm("Are you sure? This will remove all notes permanently."):
            client[DB_NAME].drop_collection(COLLECTION_NAME)
            st.success("Collection dropped.")
            st.experimental_rerun()

# -------------------------
# Footer / hints
# -------------------------
st.markdown("---")
st.caption("This Notes App is made by Atharva Yogesh Deorukhkar")
