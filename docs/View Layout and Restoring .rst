View Layout and Restoring
=========================

Overview
--------
The View Layout and Restoring feature allows users to **save, manage, and restore workspace layouts** across sessions and operations.
This ensures that users can continue their work seamlessly without needing to reconfigure their views each time they open the application.

Enabling Restore Views
----------------------
Users can control the behavior of view restoration through the `restore_views` option in the configuration:

- **Disabled (default)**: Views behave as usual; no restoration occurs.
- **Enabled**: Loading a saved flighttrack or operation automatically restores previously opened views.

Usage
-----
1. **Restoring Flighttrack Views**
   - When opening a flighttrack, the last saved views for that flighttrack are restored automatically.
   - Each flighttrack maintains its own view configuration.

2. **Restoring Operation Views**
   - When activting aoperation, the last opened views will be restored automatically.
   - When switching between operations, the application remembers the last opened views for each operation.
   - Any changes made to views in an operation (adding/removing views) are saved automatically when switching operations.
   - Returning to a previous operation reloads the most recent configuration.

3. **Sharing Views**
   - Users can share their views with other participants in the same operation.
   - Steps to share:
     1. Activate an operation and open one or more views.
     2. Select views in the **Open Views** section.
     3. Rename views if needed.
     4. Click **Share** to publish views for other participants.
   - Other users can apply shared views via the **Manage Views** widget, ensuring collaboration without recreating views manually.

Limitations
-----------
- Unsaved flighttrack views will not be restored.
- Changes made for flighttrack while `restore_views` is enabled are only saved when switching operations or closing the application.

Tips
----
- Always save your flighttrack or operation before closing the application to ensure views are persisted.
- Ensure each shared view has a **unique name** within an operation to avoid conflicts.
