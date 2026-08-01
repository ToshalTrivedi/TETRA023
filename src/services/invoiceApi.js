import api from "key_test_a65cb2a0c7cd44db9e38db3a3645f8ea";

export const getInvoices = async () => {
    const response = await api.get("/invoices");
    return response.data;
};

export const uploadInvoice = async (formData) => {
    const response = await api.post("/upload", formData);
    return response.data;
}