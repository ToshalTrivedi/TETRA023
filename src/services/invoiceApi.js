import api from "./api";

const demoInvoices = [
  {
    invoiceId: "INV001",
    vendor: "ABC Traders",
    amount: "₹15,000",
    risk: "High",
  },
  {
    invoiceId: "INV002",
    vendor: "XYZ Pvt Ltd",
    amount: "₹8,200",
    risk: "Low",
  },
  {
    invoiceId: "INV003",
    vendor: "Delta Supplies",
    amount: "₹22,450",
    risk: "Medium",
  },
];

export const uploadInvoice = async (formData) => {
  const file = formData.get("file");

  try {
    const response = await api.post("/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    console.warn("Upload API unavailable, using demo mode.", error);

    return {
      success: true,
      message: `Demo upload accepted for ${file?.name || "invoice"}`,
      data: {
        filename: file?.name || "invoice.pdf",
        status: "demo-uploaded",
      },
    };
  }
};

export const getInvoices = async () => {
  try {
    const response = await api.get("/invoices");
    return response.data;
  } catch (error) {
    console.warn("Invoices API unavailable, using demo data.", error);
    return demoInvoices;
  }
};