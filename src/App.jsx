import { Toaster } from "react-hot-toast";

import AppRoutes from "./routes/AppRoutes";

function App() {
    return (
        <>
            <AppRoutes />
            <Toaster
                position="top-right"
                reverseOrder={false}
                toastOptions={{
                    duration: 3000,
                    style: {
                        borderRadius: "14px",
                        background: "#111827",
                        color: "#fff",
                    },
                }}
            />
        </>
    );
}

export default App;