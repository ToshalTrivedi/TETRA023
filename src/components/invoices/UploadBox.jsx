import { useState } from "react";
import { UploadCloud } from "lucide-react";

const supportedFormats = [".pdf", ".png", ".jpg", ".jpeg"];

export default function UploadBox({ onFileSelect }) {
  const [isDragging, setIsDragging] = useState(false);

  const isSupportedFile = (file) => {
    const fileName = file?.name?.toLowerCase() || "";
    return supportedFormats.some((format) => fileName.endsWith(format));
  };

  const handleSelectedFile = (file) => {
    if (!file) return;

    if (!isSupportedFile(file)) {
      return;
    }

    onFileSelect(file);
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    handleSelectedFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];
    handleSelectedFile(file);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`bg-white rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
        isDragging
          ? "border-indigo-500 bg-indigo-50 shadow-lg"
          : "border-gray-300"
      }`}
    >
      <UploadCloud
        size={60}
        className="mx-auto text-indigo-600 mb-5"
      />

      <h2 className="text-2xl font-semibold">
        Upload Invoice
      </h2>

      <p className="text-gray-500 mt-2">
        Drag and drop a PDF, PNG or JPG file here, or browse to upload.
      </p>

      <input
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        onChange={handleChange}
        className="hidden"
        id="invoiceUpload"
      />

      <label
        htmlFor="invoiceUpload"
        className="mt-8 inline-block cursor-pointer bg-indigo-600 text-white px-6 py-3 rounded-xl hover:bg-indigo-700"
      >
        Browse Files
      </label>
    </div>
  );
}