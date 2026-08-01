import { useState } from "react";

import UploadBox from "../../components/invoices/UploadBox";
import FilePreview from "../../components/invoices/FilePreview";
import UploadActions from "../../components/invoices/UploadActions";
import { uploadInvoice } from "../../services/invoiceApi";
import toast from "react-hot-toast";

export default function UploadInvoices() {

  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleCancel() {
    setSelectedFile(null);
  }

  async function handleUpload() {

    if (!selectedFile) return;

    try {

        setLoading(true);

        const formData = new FormData();

        formData.append("file", selectedFile);

        const response = await uploadInvoice(formData);

        toast.success(response?.message || "Invoice uploaded successfully");

        console.log(response);

        setSelectedFile(null);

    }

    catch(error){

        console.error(error);

        toast.error(error?.message || "Upload failed");

    }

    finally{

        setLoading(false);

    }

}

  return (

    <div>

      <h1 className="text-4xl font-bold">
        Upload Invoices
      </h1>

      <p className="text-gray-500 mt-2 mb-8">
        Upload invoice documents for OCR extraction and AI risk analysis.
      </p>

      <UploadBox onFileSelect={setSelectedFile} />

      <FilePreview
        file={selectedFile}
        removeFile={handleCancel}
      />

      <UploadActions
        file={selectedFile}
        onUpload={handleUpload}
        onCancel={handleCancel}
        loading={loading}
      />

    </div>

  );

}