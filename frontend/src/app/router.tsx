import { createBrowserRouter } from "react-router-dom";

import { LoginPage } from "@/features/auth/LoginPage";
import { AdminPortalHome } from "@/features/admin-portal/AdminPortalHome";
import { BuyerPortalHome } from "@/features/buyer-portal/BuyerPortalHome";
import { MinePortalHome } from "@/features/mine-portal/MinePortalHome";

import { LandingPage } from "./LandingPage";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/mine", element: <MinePortalHome /> },
  { path: "/buyer", element: <BuyerPortalHome /> },
  { path: "/admin", element: <AdminPortalHome /> },
]);
