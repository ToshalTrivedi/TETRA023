export default function FilterBar({
    status,
    setStatus,
}){

    return(

        <select

        value={status}

        onChange={(e)=>setStatus(e.target.value)}

        className="border rounded-xl px-4 py-3"

        >

            <option value="">All Status</option>

            <option>Pending</option>

            <option>Processed</option>

            <option>Rejected</option>

        </select>

    )

}