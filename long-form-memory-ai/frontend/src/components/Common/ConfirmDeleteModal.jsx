import React from "react";
import { createPortal } from "react-dom";

export default function ConfirmDeleteModal({ open, onClose, onConfirm }) {
  const [inputValue, setInputValue] = React.useState("");
  const isDeleteEnabled = inputValue === "DELETE";

  React.useEffect(() => {
    if (!open) {
      setInputValue("");
    }
  }, [open]);

  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
      <div className="bg-neutral-900 border border-red-800 rounded-lg shadow-xl p-8 max-w-md w-[90vw] flex flex-col items-center justify-center">
        <h2 className="text-xl font-bold mb-2 flex items-center" style={{ color: '#f87171' }}>
          <svg className="h-6 w-6 mr-2" fill="none" stroke="#f87171" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" /></svg>
          Delete Account
        </h2>
        <p className="text-neutral-200 mb-4 text-center">Deleting your account will permanently remove all your data, chats, conversations, and memories. This action cannot be undone.</p>
        <div className="w-full mb-4">
          <label className="block text-neutral-300 text-sm mb-2">
            Type <span className="font-bold text-red-400">DELETE</span> to confirm:
          </label>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded text-neutral-200 focus:outline-none focus:border-red-600"
            placeholder="DELETE"
            autoFocus
          />
        </div>
        <div className="flex justify-end space-x-2 w-full">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-neutral-700 text-neutral-200 hover:bg-neutral-600 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!isDeleteEnabled}
            className="px-4 py-2 rounded font-semibold border transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ 
              background: isDeleteEnabled ? '#b91c1c' : '#4b5563', 
              borderColor: isDeleteEnabled ? '#991b1b' : '#6b7280', 
              color: 'white' 
            }}
            onMouseOver={e => isDeleteEnabled && (e.currentTarget.style.background = '#991b1b')}
            onMouseOut={e => isDeleteEnabled && (e.currentTarget.style.background = '#b91c1c')}
          >
            Yes, Delete
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}