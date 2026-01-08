import { atom } from "jotai";

export const sidebarOpenAtom = atom(true);
export const themeAtom = atom<"light" | "dark">("light");
export const isRecordingAtom = atom(false);
