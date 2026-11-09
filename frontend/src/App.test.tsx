import { afterEach,expect,it,vi } from "vitest"
import { cleanup,fireEvent,render,screen } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"
import App from "./App"
afterEach(()=>{cleanup();vi.unstubAllGlobals()})
it("starts in Urdu, validates required credentials and can reveal the password",async()=>{
 vi.stubGlobal("fetch",vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:"Authentication required"}),{status:401})))
 render(<App/>)
 const username=await screen.findByLabelText("صارف کا نام")
 expect(document.documentElement.dir).toBe("rtl")
 fireEvent.click(screen.getByRole("button",{name:"لاگ اِن کریں"}))
 expect(await screen.findByText("صارف کا نام درج کریں")).toBeVisible()
 fireEvent.change(username,{target:{value:"owner"}})
 const password=screen.getByLabelText("پاس ورڈ",{selector:"input"})
 expect(password).toHaveAttribute("type","password")
 fireEvent.click(screen.getByRole("button",{name:"پاس ورڈ دکھائیں یا چھپائیں"}))
 expect(password).toHaveAttribute("type","text")
 fireEvent.click(screen.getByRole("button",{name:"English"}))
 expect(screen.getByRole("heading",{name:"Welcome back"})).toBeVisible()
 expect(document.documentElement.dir).toBe("ltr")
})
