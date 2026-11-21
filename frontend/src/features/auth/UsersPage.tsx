import { useEffect, useRef, useState } from "react";
import { Plus, Users } from "lucide-react";
import { api } from "../../shared/api/client";
import { EmptyState } from "../../shared/components/EmptyState";
import { ListPagination } from "../../shared/components/ListPagination";
import { AccountDialog } from "./AccountDialog";
import { accountRoles, accountStatuses, type Account, type AccountsPage } from "./accounts-model";

export function UsersPage() {
  const [data, setData] = useState<AccountsPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [revision, setRevision] = useState(0);
  const [editor, setEditor] = useState<Account | "new" | null>(null);
  const addAccount = useRef<HTMLButtonElement>(null);
  const reload = () => setRevision((value) => value + 1);
  const closeEditor = () => {
    setEditor(null);
    if (document.activeElement === document.body) addAccount.current?.focus();
  };

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    api<AccountsPage>(`/admin/users?page=${page}&page_size=${pageSize}`, { signal: controller.signal })
      .then((result) => { if (!controller.signal.aborted) setData(result); })
      .catch((err: unknown) => {
        if (!controller.signal.aborted)
          setError(err instanceof Error ? err.message : "Nie można pobrać listy kont.");
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [page, pageSize, revision]);

  return (
    <section className="widget accounts-page" aria-labelledby="accounts-heading" aria-busy={loading}>
      <header className="accounts-header">
        <h2 id="accounts-heading">Konta użytkowników</h2>
        <button ref={addAccount} className="button button-primary" onClick={() => setEditor("new")}>
          <Plus size={17} aria-hidden="true" /> Dodaj konto
        </button>
      </header>
      {loading && <p role="status">Pobieranie kont…</p>}
      {error && (
        <div role="alert" className="accounts-error">
          <p>{error}</p>
          <button className="button button-secondary" onClick={reload}>Spróbuj ponownie</button>
        </div>
      )}
      {!loading && !error && data?.items.length === 0 && (
        <EmptyState icon={Users} title="Ta strona jest pusta" description="Wróć do poprzedniej strony lub dodaj konto." />
      )}
      {!loading && !error && data && data.items.length > 0 && (
        <ul className="account-list">
          {data.items.map((item) => (
            <li className="account-row" key={item.id}>
              <div className="account-identity">
                <h3>{item.display_name}</h3>
                <span>{item.username}</span>
                {item.email && <span>{item.email}</span>}
              </div>
              <div className="account-access">
                <span>{accountRoles[item.role]}</span>
                <span className="account-status" data-status={item.status}>{accountStatuses[item.status]}</span>
              </div>
              <button className="button button-secondary" aria-label={`Edytuj konto ${item.username}`}
                onClick={() => setEditor(item)}>
                Edytuj
              </button>
            </li>
          ))}
        </ul>
      )}
      {data && data.total > 0 && !error && (
        <ListPagination
          page={page}
          pageSize={pageSize}
          total={data.total}
          loading={loading}
          label="Użytkownicy"
          onPage={setPage}
          onPageSize={(size) => { setPageSize(size); setPage(1); }}
        />
      )}
      {editor && (
        <AccountDialog
          account={editor === "new" ? null : editor}
          onClose={closeEditor}
          onSaved={reload}
        />
      )}
    </section>
  );
}
