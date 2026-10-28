import { useState } from "react";
import { parseRiotId } from "../api";

export function SearchForm({ onSearch, loading }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState(null);

  function handleSubmit(e) {
    e.preventDefault();
    const id = parseRiotId(value);
    if (!id) {
      setError("Enter a Riot ID like Name#TAG");
      return;
    }
    setError(null);
    onSearch(id);
  }

  return (
    <form onSubmit={handleSubmit} className="search">
      <label className="search-field" htmlFor="riot-id">
        <span>Riot ID</span>
        <input
          id="riot-id"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Name#TAG"
          autoComplete="off"
        />
      </label>
      <button type="submit" disabled={loading}>
        {loading ? "Loading…" : "Search"}
      </button>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </form>
  );
}
