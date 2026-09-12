// Vulnerable Next.js 14/15 App Router example

"use server"

// 1. Critical: Secret exposed in client-side NEXT_PUBLIC_ env
export const STRIPE_SECRET = process.env.NEXT_PUBLIC_SECRET_KEY;

// 2. High: Server action with zero auth check
export async function deleteUserAccount(userId: string) {
  // Directly deletes without checking session or calling auth()
  return await db.user.delete({ where: { id: userId } });
}

// 3. Critical: Raw SQL injection via template string interpolation
export async function getInvoicesUnsafe(companyId: string) {
  return await db.$queryRawUnsafe(`SELECT * FROM invoices WHERE company_id = '${companyId}'`);
}

// 4. Medium: Open redirect via user-controlled URL parameter
export async function handleUserRedirect(req: any) {
  const target = req.searchParams.get("returnUrl");
  return redirect(target);
}

// 5. High: SSRF via unvalidated fetch
export async function fetchWebhookContent(req: any) {
  return await fetch(req.body.webhookUrl);
}
