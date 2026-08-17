import { redirect } from "next/navigation";

/**
 * Root page — redirects to /dashboard (which itself redirects to /login
 * if unauthenticated).
 */
export default function Home() {
  redirect("/dashboard");
}
