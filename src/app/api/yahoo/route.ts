import { NextResponse } from "next/server";

const ALLOWED_HOSTS = new Set(["query1.finance.yahoo.com", "query2.finance.yahoo.com"]);

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const target = searchParams.get("url");

  if (!target) {
    return NextResponse.json({ error: "Missing url parameter" }, { status: 400 });
  }

  let targetUrl: URL;

  try {
    targetUrl = new URL(target);
  } catch {
    return NextResponse.json({ error: "Invalid url parameter" }, { status: 400 });
  }

  if (!ALLOWED_HOSTS.has(targetUrl.hostname)) {
    return NextResponse.json({ error: "Host is not allowed" }, { status: 400 });
  }

  const response = await fetch(targetUrl, {
    headers: {
      accept: "application/json",
      "user-agent": "PocketScreener/1.0",
    },
    next: {
      revalidate: 60,
    },
  });

  const body = await response.text();

  return new NextResponse(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
      "cache-control": "public, max-age=60",
    },
  });
}
