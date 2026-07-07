# Guia de Arquitetura Frontend — React + TypeScript + Tailwind v4

> Baseado na análise do **Library-Frontend** (referência principal) e **ParkManager-Frontend** (referência secundária).  
> Este documento define a estrutura, padrões e melhores práticas a adotar em novos projetos.

---

## Stack

| Camada | Biblioteca | Versão |
|--------|-----------|--------|
| Framework | React | 19 |
| Linguagem | TypeScript | 5.9+ |
| Build | Vite | 7 |
| Roteamento | React Router DOM | 7 |
| Estilização | Tailwind CSS v4 + DaisyUI v5 | — |
| Ícones | Lucide React | — |
| HTTP | Axios | 1.x |
| Server State | TanStack React Query | 5 |
| Formulários | React Hook Form + Zod | — |
| Animações | tailwindcss-animate | — |

> **TypeScript é obrigatório.** O ParkManager usa `.jsx` sem tipagem — evitar em projetos novos.

---

## Estrutura de Pastas

```
src/
├── components/
│   ├── layout/          # AppLayout, Sidebar, Header (um por projeto)
│   └── ui/              # Componentes genéricos reutilizáveis
│       ├── Button.tsx
│       ├── ConfirmDialog.tsx
│       ├── FeedbackToast.tsx
│       ├── GlobalRequestIndicator.tsx
│       ├── Pagination.tsx
│       └── DetailsSidePanel.tsx
│
├── features/            # ← CORAÇÃO DA APLICAÇÃO
│   ├── auth/            # Autenticação (se existir)
│   │   ├── AuthContext.tsx
│   │   └── PrivateRoute.tsx
│   ├── books/
│   │   ├── hooks/
│   │   │   ├── useBooks.ts        # useQuery para listagem
│   │   │   └── useBookMutations.ts # useMutation para create/update/delete
│   │   ├── components/
│   │   │   ├── BookTable.tsx
│   │   │   ├── BookForm.tsx
│   │   │   └── BookDetails.tsx
│   │   └── index.ts               # re-exports públicos da feature
│   └── authors/
│       ├── hooks/
│       └── components/
│
├── pages/               # Orquestração apenas — sem lógica de negócio
│   ├── BooksPage.tsx    # usa hooks de features/, compõe componentes
│   ├── AuthorsPage.tsx
│   └── ...
│
├── services/            # Camada HTTP centralizada
│   ├── api.ts           # instância axios + interceptors + normalizeApiError
│   ├── booksApi.ts
│   ├── authorsApi.ts
│   └── requestTracker.ts
│
├── schemas/             # Schemas Zod para formulários
│   └── forms.ts
│
├── types/               # Tipos TypeScript globais
│   ├── api.ts           # ApiError, ValidationErrorResponse
│   ├── bookDtos.ts
│   ├── authorDtos.ts
│   └── commonDtos.ts    # PagedResult<T>, tipos compartilhados
│
├── utils/               # Funções puras sem side-effects
│   ├── constants.ts     # APP_CONFIG, ROUTES
│   └── formErrors.ts    # applyFieldErrors
│
├── lib/
│   └── queryClient.ts   # Configuração global do QueryClient
│
├── index.css            # Tailwind @theme, @variant dark, fontes
├── main.tsx             # Providers: QueryClientProvider > BrowserRouter
└── App.tsx              # Definição de rotas
```

---

## Camada HTTP — `services/`

### `api.ts` — instância única do Axios

```typescript
// src/services/api.ts
import axios from "axios";
import { APP_CONFIG } from "../utils/constants";
import type { ApiError, ValidationErrorResponse } from "../types/api";
import { requestTracker } from "./requestTracker";

const normalizeApiError = (error: unknown): ApiError => {
  if (!axios.isAxiosError(error)) {
    const fallback = new Error("Erro inesperado de comunicação.") as ApiError;
    fallback.raw = error;
    return fallback;
  }

  const status = error.response?.status;
  const data = error.response?.data as unknown;
  const defaultMessage = "Falha ao processar a requisição.";

  if (typeof data === "string") {
    const apiError = new Error(data || defaultMessage) as ApiError;
    apiError.status = status;
    apiError.raw = data;
    return apiError;
  }

  if (typeof data === "object" && data !== null) {
    const maybeValidation = data as ValidationErrorResponse;
    const fieldErrors = maybeValidation.errors;
    const fieldMessages = fieldErrors
      ? Object.values(fieldErrors).flat().filter(Boolean)
      : [];
    const message =
      fieldMessages[0] ?? maybeValidation.title ?? defaultMessage;

    const apiError = new Error(message) as ApiError;
    apiError.status = status;
    apiError.fieldErrors = fieldErrors;
    apiError.raw = data;
    return apiError;
  }

  const apiError = new Error(defaultMessage) as ApiError;
  apiError.status = status;
  apiError.raw = data;
  return apiError;
};

export const api = axios.create({
  baseURL: APP_CONFIG.apiBaseUrl,
  headers: { "Content-Type": "application/json" },
});

// Interceptor de request: inicia indicador global de carregamento
api.interceptors.request.use((config) => {
  requestTracker.start();
  return config;
});

// Interceptor de response: finaliza indicador + normaliza erros
api.interceptors.response.use(
  (response) => {
    requestTracker.end();
    return response;
  },
  (error) => {
    requestTracker.end();
    return Promise.reject(normalizeApiError(error));
  },
);
```

**Por que uma instância única:**
- `baseURL` configurada uma vez via `VITE_API_BASE_URL`
- Interceptors aplicados globalmente — sem repetição de `Authorization` header em cada chamada
- Normalização de erro centralizada — todas as chamadas lançam `ApiError` tipado

**Comparação com ParkManager:** o ParkManager chama `axios.get(${API_BASE_URL}/rota, { headers: { Authorization: ... } })` diretamente em cada hook. Isso gera repetição do header em cada arquivo e erros não normalizados (`catch (err) { setErro(err) }`).

---

### `services/<recurso>Api.ts` — um arquivo por recurso

```typescript
// src/services/booksApi.ts
import { api } from "./api";
import type { BookCreateDto, BookGetDto, BookUpdateDto } from "../types/bookDtos";
import type { PagedResult } from "../types/commonDtos";

export const booksApi = {
  async list(page: number, size: number) {
    const { data } = await api.get<PagedResult<BookGetDto>>("/book", {
      params: { page, size },
    });
    return data;
  },
  async detail(id: string) {
    const { data } = await api.get<BookGetDto>(`/book/${id}`);
    return data;
  },
  async create(payload: BookCreateDto) {
    const { data } = await api.post<BookGetDto>("/book", payload);
    return data;
  },
  async update(id: string, payload: BookUpdateDto) {
    const { data } = await api.put<BookGetDto>(`/book/${id}`, payload);
    return data;
  },
  async remove(id: string) {
    await api.delete(`/book/${id}`);
  },
};
```

**Regras:**
- Só chama `api.*` — nunca `axios.*` diretamente
- Retorna o `data` desempacotado — quem chama não precisa saber de `response.data`
- Tipagem explícita no genérico do axios — TypeScript infere o retorno automaticamente
- Sem lógica de negócio — sem `if`, sem `try/catch`, sem estado

---

### `requestTracker.ts` — indicador global de requisições

Pub/sub leve para rastrear quantas requisições estão em voo, sem Redux ou Context:

```typescript
type Listener = (activeRequests: number) => void;

let activeRequests = 0;
const listeners = new Set<Listener>();

const notify = () => listeners.forEach((l) => l(activeRequests));

export const requestTracker = {
  start() { activeRequests += 1; notify(); },
  end()   { activeRequests = Math.max(0, activeRequests - 1); notify(); },
  getCount() { return activeRequests; },
  subscribe(listener: Listener) {
    listeners.add(listener);
    listener(activeRequests);
    return () => listeners.delete(listener); // cleanup
  },
};
```

Usado pelo `GlobalRequestIndicator` — uma barra animada no topo da tela enquanto qualquer requisição estiver ativa.

---

## Tipagem — `types/`

### `types/api.ts`

```typescript
export type ValidationErrorResponse = {
  type?: string;
  title?: string;
  status?: number;
  errors?: Record<string, string[]>;
  traceId?: string;
};

export type ApiError = Error & {
  status?: number;
  fieldErrors?: Record<string, string[]>;
  raw?: unknown;
};

export const isApiError = (error: unknown): error is ApiError =>
  typeof error === "object" && error !== null && "message" in error;
```

### `types/commonDtos.ts`

```typescript
export type PagedResult<T> = {
  items: T[];
  totalCount: number;
  page: number;
  size: number;
  totalPages: number;
};
```

### DTOs por recurso

```typescript
// types/bookDtos.ts
export type BookGetDto = {
  idBook: string;
  title: string;
  isbn: string;
  year: number;
  quantity: number;
  author: AuthorSummaryDto;
};

export type BookCreateDto = Omit<BookGetDto, "idBook" | "author"> & {
  idAuthor: string;
};

export type BookUpdateDto = BookCreateDto;
```

---

## Validação de Formulários — `schemas/forms.ts`

Todos os schemas Zod em um único arquivo (ou separados por feature se crescer muito):

```typescript
import { z } from "zod";

export const bookSchema = z.object({
  title: z.string().min(3, "Mínimo 3 caracteres.").max(300),
  isbn: z.string().length(13, "ISBN deve ter 13 dígitos."),
  year: z.number().int().min(0).max(32767),
  quantity: z.number().int().min(0),
  idAuthor: z.uuid("Selecione um autor válido."),
});

export type BookFormValues = z.infer<typeof bookSchema>;
```

**Uso com React Hook Form:**
```typescript
const form = useForm<BookFormValues>({
  resolver: zodResolver(bookSchema),
  defaultValues: { title: "", isbn: "", year: 0, quantity: 0, idAuthor: "" },
});
```

---

## Erros de Formulário do Servidor — `utils/formErrors.ts`

Quando o backend retorna erros de validação por campo (`errors: { Title: ["..."] }`), aplica diretamente no form:

```typescript
export const applyFieldErrors = <T extends FieldValues>(
  error: ApiError,
  setError: UseFormSetError<T>,
  keyMap: Record<string, string>,  // mapeamento backend → campo do form
) => {
  if (!error.fieldErrors) return;
  Object.entries(error.fieldErrors).forEach(([key, messages]) => {
    const mapped = keyMap[key];
    if (!mapped || messages.length === 0) return;
    setError(mapped as FieldPath<T>, { type: "server", message: messages[0] });
  });
};

// Uso na página:
const bookFieldMap = { Title: "title", Isbn: "isbn", IdAuthor: "idAuthor" };
applyFieldErrors(error, form.setError, bookFieldMap);
```

---

## Server State — Hooks de Feature

Em vez de lógica dentro das pages, cada feature expõe hooks:

```typescript
// src/features/books/hooks/useBooks.ts
import { useQuery } from "@tanstack/react-query";
import { booksApi } from "../../../services/booksApi";

export const useBooks = (page: number, size: number) =>
  useQuery({
    queryKey: ["books", page, size],
    queryFn: () => booksApi.list(page, size),
  });

export const useBook = (id: string) =>
  useQuery({
    queryKey: ["books", id],
    queryFn: () => booksApi.detail(id),
    enabled: !!id,
  });
```

```typescript
// src/features/books/hooks/useBookMutations.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { booksApi } from "../../../services/booksApi";

export const useCreateBook = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: booksApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["books"] }),
  });
};

export const useDeleteBook = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: booksApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["books"] }),
  });
};
```

**Page limpa de orquestração:**
```typescript
// src/pages/BooksPage.tsx
export const BooksPage = () => {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useBooks(page, PAGE_SIZE);
  const createBook = useCreateBook();
  const deleteBook = useDeleteBook();

  // só orquestra — sem useEffect de fetch, sem axios, sem estado de loading manual
  return ( ... );
};
```

**Comparação com ParkManager:** cada hook do ParkManager (`useGetAcessos`, `useCreateEstacionamento`) gerencia seu próprio `useState([])`, `setLoading`, `setErro` e faz `useEffect` com axios. Com React Query isso some — cache, loading, erro e refetch são automáticos.

---

## QueryClient — `lib/queryClient.ts`

```typescript
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 20, // 20s de cache
    },
  },
});
```

---

## Estilização — Tailwind CSS v4

### Como funciona no v4

No Tailwind v4 **não há `tailwind.config.js`**. Toda configuração fica no `index.css`:

```css
@import "tailwindcss";
@plugin "tailwindcss-animate";
@plugin "daisyui";

/* Variante dark ativada por classe .dark no <html> */
@custom-variant dark (&:where(.dark, .dark *));
```

### Design Tokens — `@theme`

Cores semânticas definidas como CSS custom properties, usáveis diretamente como classes Tailwind:

```css
@theme {
  /* Superfícies */
  --color-fundo-pagina: #dbe6f0;
  --color-fundo-superficie: #ffffff;
  --color-fundo-superficie-suave: #dce6ef;
  --color-borda-padrao: #dbe6f0;

  /* Texto */
  --color-texto-principal: #1e293b;
  --color-texto-secundario: #94a3b8;

  /* Destaque (accent color) */
  --color-destaque: #fb923c;
  --color-destaque-hover: #f97316;
  --color-destaque-suave: #fff7ed;

  /* Status */
  --color-sucesso: #10b981;
  --color-aviso: #f59e0b;
  --color-erro: #f43f5e;
  --color-info: #0ea5e9;
}

/* Tema dark sobrescreve os tokens — a UI adapta automaticamente */
@variant dark {
  --color-fundo-pagina: #0f172a;
  --color-fundo-superficie: #1e293b;
  --color-texto-principal: #f8fafc;
  /* ... */
}
```

**Resultado:** componentes usam `bg-fundo-superficie text-texto-principal border-borda-padrao` — sem hardcode de `#ffffff` ou `dark:bg-slate-800` espalhado pelo código.

### Dark Mode

Controlado por classe `.dark` no `<html>`, persistido no `localStorage`:

```typescript
// No AppLayout:
const toggleDarkMode = () => {
  setIsDarkMode((current) => {
    const next = !current;
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("app-tema-dark", next ? "1" : "0");
    return next;
  });
};
```

### DaisyUI v5

Usado para componentes de dialog (`<dialog>` nativo via `showModal()`). **Não usar** os componentes prontos do DaisyUI para coisas que o projeto já tem customizadas (botões, cards, inputs) — o Tailwind puro com os tokens semânticos dá mais controle visual.

### Boas práticas de classe

```tsx
// ✅ Extrair classes repetidas para variável
const panelClass = "rounded-3xl border border-borda-padrao bg-fundo-superficie p-6 shadow-sm";

// ✅ Função para classes condicionais
const menuButtonClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-[10px] px-4 py-3 font-semibold transition ${
    isActive
      ? "bg-destaque text-texto-principal"
      : "text-texto-secundario hover:bg-destaque-suave"
  }`;

// ❌ Evitar: inline ternário longo diretamente no JSX
<div className={`... ${condition ? "muitas classes aqui e mais aqui" : "outras classes"}`} />
```

---

## Componentes UI Reutilizáveis

### `FeedbackToast` — notificação temporária

```tsx
// Uso na page:
const [feedback, setFeedback] = useState<{ type: "success"|"error"; message: string } | null>(null);

useEffect(() => {
  if (!feedback) return;
  const timer = setTimeout(() => setFeedback(null), 3000);
  return () => clearTimeout(timer);
}, [feedback]);

// No JSX:
{feedback && <FeedbackToast {...feedback} onClose={() => setFeedback(null)} />}
```

> **Alternativa recomendada para novos projetos:** biblioteca `sonner` (1KB, zero config, belíssima por padrão) ou `react-hot-toast`. O ParkManager usa `react-toastify` — funciona, mas é mais pesado e precisa do `<ToastContainer />` no App.

### `ConfirmDialog` — dialog de confirmação

Usa `<dialog>` nativo HTML5 com `showModal()` — sem portais React, sem biblioteca extra:

```tsx
// Abrir/fechar via DOM:
const openDialog = (id: string) =>
  (document.getElementById(id) as HTMLDialogElement)?.showModal();

// Uso:
<ConfirmDialog
  id="delete-book-modal"
  title="Excluir livro"
  description="Essa ação não pode ser desfeita."
  confirmTone="danger"
  isLoading={deleteBook.isPending}
  onConfirm={() => deleteBook.mutate(bookToDelete.id)}
/>
```

### `GlobalRequestIndicator` — barra de loading global

```tsx
export const GlobalRequestIndicator = () => {
  const isFetching = useIsFetching();     // queries do React Query
  const isMutating = useIsMutating();     // mutations do React Query
  const [active, setActive] = useState(requestTracker.getCount());

  useEffect(() => requestTracker.subscribe(setActive), []);

  if (isFetching === 0 && isMutating === 0 && active === 0) return null;

  return (
    <div className="fixed left-0 right-0 top-0 z-100">
      <div className="h-1 w-full animate-pulse bg-destaque" />
    </div>
  );
};
```

### `Pagination` — paginação genérica

Recebe `page`, `totalPages`, `onPageChange` — sem opinião sobre a query.

---

## Roteamento — `App.tsx`

```tsx
// Layout aninhado via Outlet — padrão React Router v6+
function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>         {/* Sidebar + Header */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/books" element={<BooksPage />} />
        <Route path="/authors" element={<AuthorsPage />} />
      </Route>

      {/* Rotas sem layout (login, etc.) */}
      <Route path="/login" element={<LoginPage />} />
    </Routes>
  );
}
```

Rotas como constantes em `utils/constants.ts`:

```typescript
export const ROUTES = {
  dashboard: "/dashboard",
  books: "/books",
  authors: "/authors",
  login: "/login",
} as const;
```

---

## Configuração de Providers — `main.tsx`

```tsx
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
```

**Ordem:** QueryClientProvider envolve o BrowserRouter para que hooks de query funcionem dentro de componentes que dependem de rota.

---

## Variáveis de Ambiente

```
# .env.example
VITE_API_BASE_URL=http://localhost:5042
```

Acesso via `import.meta.env.VITE_API_BASE_URL` — centralizado em `constants.ts`:

```typescript
export const APP_CONFIG = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL as string,
  defaultPageSize: 10,
} as const;
```

---

## O que Evitar (lições dos dois projetos)

| Antipadrão | Onde aparece | Solução |
|-----------|-------------|---------|
| `axios` chamado direto no componente/hook | ParkManager — todos os Hooks/ | Sempre via `api.*` de `services/` |
| `Authorization` header repetido em cada chamada | ParkManager | Interceptor no `api.ts` |
| `useEffect` + `useState` para fetch | ParkManager — todos os Hooks/ | `useQuery` do React Query |
| `window.location.reload()` após mutação | `CreateEstacionamento.jsx` L21 | `queryClient.invalidateQueries()` |
| Lógica de negócio dentro da page (~700 linhas) | Library — `BooksPage.tsx` | Extrair para hooks de feature |
| `catch (err) { setErro(err) }` sem normalização | ParkManager | `normalizeApiError` no interceptor |
| Classes `.jsx` sem tipagem | ParkManager inteiro | TypeScript + tipos explícitos |
| `logout` retornando JSX (`<Navigate />`) | `AuthContext.jsx` L86 | `navigate("/login")` via `useNavigate` |

---

## Checklist para Novo Projeto

- [ ] `src/services/api.ts` com instância única, interceptors e `normalizeApiError`
- [ ] Um arquivo `*Api.ts` por recurso em `services/`
- [ ] `types/api.ts` com `ApiError` e `ValidationErrorResponse`
- [ ] `types/commonDtos.ts` com `PagedResult<T>`
- [ ] `schemas/forms.ts` com schemas Zod + tipos inferidos
- [ ] `utils/formErrors.ts` com `applyFieldErrors`
- [ ] `lib/queryClient.ts` configurado
- [ ] `index.css` com tokens semânticos em `@theme` (light + dark)
- [ ] `components/ui/GlobalRequestIndicator` + `requestTracker`
- [ ] `components/ui/FeedbackToast` ou `sonner`
- [ ] `components/ui/ConfirmDialog` com `<dialog>` nativo
- [ ] `utils/constants.ts` com `APP_CONFIG` e `ROUTES`
- [ ] Hooks de feature em `features/<recurso>/hooks/` usando `useQuery`/`useMutation`
- [ ] Pages como orquestradores — sem axios, sem useEffect de fetch
