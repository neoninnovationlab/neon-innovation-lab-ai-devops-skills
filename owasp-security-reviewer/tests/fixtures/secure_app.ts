// Secure Next.js App Router example

"use server"

// 1. Secrets stored securely in server-only env
export const STRIPE_SECRET = process.env.STRIPE_SECRET_KEY;

// 2. Server action with strict session auth
export async function deleteUserAccount(userId: string) {
  const session = await auth();
  if (!session?.user || session.user.id !== userId) {
    throw new Error("Unauthorized");
  }
  return await db.user.delete({ where: { id: userId } });
}

// 3. Parameterized SQL query with auth
export async function getInvoicesSafe(companyId: string) {
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");
  return await db.query("SELECT * FROM invoices WHERE company_id = $1", [companyId]);
}

// 4. Validated redirect using domain allowlist with auth
const ALLOWED_HOSTS = ["/dashboard", "/profile", "/settings"];
export async function handleUserRedirect(target: string) {
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");
  const safeUrl = ALLOWED_HOSTS.includes(target) ? target : "/dashboard";
  return redirect(safeUrl);
}
