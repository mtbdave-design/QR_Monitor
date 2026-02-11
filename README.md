A lightweight, automated desktop utility for Windows that monitors your clipboard and instantly transforms copied text or links into a structured QR code gallery. Featuring Smart Grid logic, Permanent Gold storage, and Drag-and-Drop organization. 


✨ Key Features
📋 Real-Time Monitoring: Automatically detects new clipboard entries and generates high-quality QR codes without interrupting your workflow.
🧩 Smart Grid Gallery: A dedicated 5x3 window that keeps codes in logical order (left-to-right, top-to-bottom).
🔱 Permanent "Gold" Status: Right-click any QR code to mark it as "Permanent." These items are anchored to the top-left of your gallery and survive temporary wipes.
🖱️ Drag-and-Drop Reflow: Reorder your codes by dragging them. The gallery uses a recursive collision-prevention algorithm to "shunt" items into the next available slot.
💾 Persistent Layout: Your custom organization is saved to a local JSON config, so your gallery looks exactly the same every time you launch.
🌑 Optimized UI: Features High DPI scaling (4K support), a draggable bottom-right controller, and smooth mouse-wheel scrolling. 
🚀 Just run the file, the QR monitor allows you to pause the script so your CTRL+C (copy) command doesn't create a QR Code.
Prerequisites
Ensure you have Python 3.8+ installed. 

Project Structure
saved_qrs/: Temporary storage for new clipboard scans.
permanent/: Storage for "Gold" status codes.
qr_order_config.json: Saves your custom drag-and-drop sequence.
qr-code.ico: The application branding asset
