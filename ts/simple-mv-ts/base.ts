enum RouterActions {
    Properties,
    NotFound
}

const ActionToHash = {
    Properties: "properties",
    NotFound: "not_found"
};

const HashToAction = {
    properties: RouterActions.Properties,
    not_found: RouterActions.NotFound
};

interface BaseViewListener {
    hide: () => void;
    show: () => void;
    setRootView: (el: JQuery) => any;
    getRootView: () => JQuery;
    init: () => void;
}

interface RouterListener {
    onHashChange: (data: any) => void;
}

interface HashObject {
    action: RouterActions;
    params?: any;
}

class Hash {
    static getHashObject(hash: string): HashObject {
        let action = hash.split("/")[0];
        if (action.charAt(0) === "#") {
            action = action.substr(1);
        }

        const queryString = hash.split("/")[1];
        return {
            action: HashToAction[action] || RouterActions.NotFound,
            params: queryString ? Hash.parseParamsFrom(queryString) : ""
        };
    }

    static parseParamsFrom(queryStr: string): any {
        const params = {};
        queryStr.split("&").map(function(el){
            const pair = el.split("=");
            let k = decodeURIComponent(pair[0]);
            const v = decodeURIComponent(pair[1]);

            if (k.substr(k.length - 2) === "[]") {
                k  = k.substr(0, (k.length - 2));
                params[k] = params[k] || [];
                params[k].push(v);
            } else {
                params[k]  = v;
            }
        });
        return params;
    }
    static getHashString(hashObj: HashObject): string {
        if (typeof hashObj.params.toQuery === "function") {
            return ActionToHash[RouterActions[hashObj.action]] + "/" + hashObj.params.toQuery();
        }
        return ActionToHash[RouterActions[hashObj.action]] + "/" + $.param(hashObj.params);
    }
}

class BaseRouter {
    public listeners: RouterListener[] = [];
    public init() {
        window.onhashchange = this.onHashChange();
        this.onHashChange()(window.location.hash);
    }

    public listen(listener: RouterListener) {
        this.listeners.push(listener);
    }

    public onHashChange() {
        return (event) => {
            const hash = window.location.hash;
            const hashObj = Hash.getHashObject(hash);
            this.listeners.forEach(function(listener){
                listener.onHashChange.call(listener, hashObj);
            });
        };
    }

    static routeTo(hashObj: HashObject) {
        window.location.hash = Hash.getHashString(hashObj);
    }
}

abstract class BaseModel implements RouterListener {
    public listeners: BaseViewListener[] = [];

    constructor(protected router: BaseRouter) {
        this.router.listen(this);
    }

    abstract onHashChange(data: any): void;

    public listen(listener: BaseViewListener) {
        this.listeners.push(listener);
    }

    public hide() {
        this.listeners.forEach(function(listener){
            listener.hide.call(listener);
        });
    }

    public show() {
        this.listeners.forEach(function(listener){
            listener.show.call(listener);
        });
    }
}

abstract class BaseView implements BaseViewListener {
    abstract setRootView(el: JQuery): any;
    abstract getRootView(): JQuery;

    constructor(public model: BaseModel) {
        this.init();
        this.model.listen(this);
    }

    public abstract init(): void;

    public hide() {
        this.getRootView().addClass("hide");
    }

    public show() {
        this.getRootView().remove("hide");
    }
}
