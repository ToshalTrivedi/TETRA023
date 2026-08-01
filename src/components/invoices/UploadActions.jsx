export default function UploadActions({
  file,
  onUpload,
  onCancel,
  loading,
}) {

  return (

    <div className="flex justify-end gap-4 mt-8">

      <button
        type="button"
        onClick={onCancel}
        className="px-6 py-3 rounded-xl border border-gray-300 text-gray-700 hover:bg-gray-50"
      >
        Cancel
      </button>

      <button
        type="button"
        disabled={!file || loading}
        onClick={onUpload}
        className="px-6 py-3 rounded-xl bg-indigo-600 text-white disabled:cursor-not-allowed disabled:bg-indigo-300"
      >
        {loading ? "Uploading..." : "Upload"}
      </button>

    </div>

  );

}