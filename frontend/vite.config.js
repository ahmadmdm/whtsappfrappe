import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"

export default defineConfig({
	plugins: [vue()],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src"),
		},
	},
	define: {
		"process.env.NODE_ENV": JSON.stringify("production"),
		"process.env": "{}",
	},
	build: {
		outDir: "../whatapp/public/dist",
		emptyOutDir: true,
		cssCodeSplit: false,
		lib: {
			entry: path.resolve(__dirname, "src/main.js"),
			formats: ["iife"],
			name: "WhatappDesk",
			fileName: () => "whatapp.bundle.js",
		},
		rollupOptions: {
			output: {
				assetFileNames: (info) =>
					info.name === "style.css" ? "whatapp.bundle.css" : "[name][extname]",
			},
		},
	},
})