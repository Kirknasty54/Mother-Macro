export default function LogoutButton({className=""}) {
    return (
        <div className={`flex items-center gap-2 ${className}`}>
            <button
                className={"bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"}
            >
                Logout
            </button>
        </div>
    );
}