import { FileText, Trash2 } from "lucide-react";

export default function FilePreview({ file, removeFile }) {

  if (!file) return null;

  return (
    <div className="bg-white rounded-2xl border p-5 mt-8 flex items-center justify-between">

      <div className="flex items-center gap-4">

        <FileText className="text-indigo-600"/>

        <div>

          <h3 className="font-semibold">
            {file.name}
          </h3>

          <p className="text-sm text-gray-500">
            {(file.size / 1024).toFixed(2)} KB
          </p>

        </div>

      </div>

      <button
        onClick={removeFile}
        className="text-red-500 hover:text-red-700"
      >
        <Trash2/>
      </button>

    </div>
  );
}