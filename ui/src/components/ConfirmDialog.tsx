import React from 'react';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'warning'
}) => {
  if (!isOpen) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'danger':
        return {
          icon: '🚨',
          iconBg: 'bg-red-100',
          iconText: 'text-red-600',
          confirmBg: 'bg-red-600 hover:bg-red-700',
          titleText: 'text-red-900'
        };
      case 'warning':
        return {
          icon: '⚠️',
          iconBg: 'bg-yellow-100',
          iconText: 'text-yellow-600',
          confirmBg: 'bg-yellow-600 hover:bg-yellow-700',
          titleText: 'text-yellow-900'
        };
      case 'info':
        return {
          icon: 'ℹ️',
          iconBg: 'bg-blue-100',
          iconText: 'text-blue-600',
          confirmBg: 'bg-blue-600 hover:bg-blue-700',
          titleText: 'text-blue-900'
        };
      default:
        return {
          icon: '⚠️',
          iconBg: 'bg-yellow-100',
          iconText: 'text-yellow-600',
          confirmBg: 'bg-yellow-600 hover:bg-yellow-700',
          titleText: 'text-yellow-900'
        };
    }
  };

  const styles = getTypeStyles();

  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  return (
    <>
      {/* Scrollable backdrop overlay */}
      <div 
        className="fixed inset-0 z-[9999] overflow-y-auto"
        onClick={onClose}
      >
        {/* Background overlay */}
        <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
        
        {/* Modal positioning container */}
        <div className="flex min-h-full items-center justify-center p-4">
          {/* Modal content */}
          <div 
            className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 transform transition-all"
            onClick={(e) => e.stopPropagation()} // Prevent close when clicking inside modal
          >
            {/* Header */}
            <div className="px-6 pt-6 pb-4">
              <div className="flex items-start">
                <div className={`flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full ${styles.iconBg}`}>
                  <span className="text-2xl">{styles.icon}</span>
                </div>
                <div className="ml-4 w-full">
                  <h3 className={`text-lg leading-6 font-medium ${styles.titleText}`}>
                    {title}
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-600">
                      {message}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-6 py-4 flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-3">
              <button
                type="button"
                className="mt-3 sm:mt-0 w-full sm:w-auto inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                onClick={onClose}
              >
                {cancelText}
              </button>
              <button
                type="button"
                className={`w-full sm:w-auto inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white ${styles.confirmBg} focus:outline-none focus:ring-2 focus:ring-offset-2`}
                onClick={() => {
                  onConfirm();
                  onClose();
                }}
              >
                {confirmText}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ConfirmDialog;