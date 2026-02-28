import requests
import json

diff = '''diff --git a/backend/app/api/projects.py b/backend/app/api/projects.py
index 734bffb..e58da14 100644
--- a/backend/app/api/projects.py
+++ b/backend/app/api/projects.py
@@ -288,10 +288,15 @@ async def get_git_commits(
         raise HTTPException(500, f"Failed to get git commits: {str(e)}")


+# Checkout git commit endpoint that accepts commit_hash in request body        
+class CheckoutRequest(BaseModel):
+    commit_hash: str
+
+
 @router.post("/{project_id}/git/checkout", tags=["Projects"])
 async def checkout_git_version(
     project_id: str,
-    commit_hash: str,
+    request: CheckoutRequest,
     db: Session = Depends(get_db),
     current_user: Optional[User] = Depends(get_current_user),
 ):
@@ -306,7 +311,7 @@ async def checkout_git_version(
             raise HTTPException(403, "Access denied")

     try:
-        success = await project_service.checkout_git_version(project_id, commit_hash)
+        success = await project_service.checkout_git_version(project_id, request.commit_hash)
         return {"code": 200, "data": {"success": success}}
     except Exception as e:
         raise HTTPException(500, f"Failed to checkout git version: {str(e)}")  
diff --git a/backend/app/services/project_service.py b/backend/app/services/project_service.py
index 9d3a9d7..4169baf 100644
--- a/backend/app/services/project_service.py
+++ b/backend/app/services/project_service.py
@@ -110,6 +110,12 @@ class ProjectService:
         if not project:
             return False

+        # Delete associated versions first to avoid foreign key constraint issues
+        from app.models.version import Version
+        versions = self.db.query(Version).filter(Version.project_id == project_id).all()
+        for version in versions:
+            self.db.delete(version)
+'''

prompt = f"请分析以下两个git提交之间的代码变化，总结修改的逻辑和目的：\n\n{diff}"

response = requests.post(
    'http://localhost:8000/api/v1/chat/ask',
    json={'question': prompt, 'chat_mode': 'freeform'}
)

print(response.json())
