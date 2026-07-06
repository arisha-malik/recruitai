# RecruitAI - Frontend Portal

The client portal for **RecruitAI**, built using **Next.js 16**, **React 19**, **TypeScript**, and **Tailwind CSS**.

---

## Technical Stack

* **Framework**: Next.js (App Router)
* **Styling**: Tailwind CSS
* **API Client**: Axios (configured with auto JWT attaching and 401 redirect handlers)
* **Icons**: Lucide React

---

## Local Development Setup

### 1. Prerequisites
Ensure you have **Node.js 20+** installed on your system.

### 2. Configure Environment Variables
Create a `.env.local` file inside the `frontend/` directory (or use `.env.example` as a template):

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Installation
Install the project dependencies:

```bash
npm install
```

### 4. Running the Development Server
Launch the local Next.js server (runs on `http://localhost:3000` by default):

```bash
npm run dev
```

The portal connects directly to the FastAPI backend running on `http://127.0.0.1:8000`.

---

## Directory Overview

* `src/app/` - Core routing pages (Login, Dashboard, Candidates, Jobs, Assistants, Analytics)
* `src/components/` - Sidebar, Navbar, and layout shells
* `src/components/ui/` - Highly polished, reusable theme components (Card, Table, Loading, Badges)
* `src/lib/api.ts` - Centralized Axios client
