export function Notice({children,error=false}:{children:React.ReactNode,error?:boolean}){return <div className={'notice '+(error?'error':'')} role={error?'alert':undefined}>{children}</div>}
